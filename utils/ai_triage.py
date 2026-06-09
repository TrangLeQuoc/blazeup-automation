"""AI failure-triage for BlazeUp test runs (post-run, log-only).

Reads a run's ``test.log``, extracts only the FAILED/ERROR parts (plus a little
context around each), then asks an LLM to classify *why* each failure happened
using a project-specific "playbook". Writes a human-readable ``ai_triage.md``
next to the log and prints a short table to the console.

Why post-run + log-only (not in-test):
- No API calls on the hot path → tests stay fast, deterministic, and free.
- The log is already structured ("time | LEVEL | TC-id | location | message")
  and masks secrets (passwords show as ``***``), so it is cheap to filter and
  safe-ish to send to a cloud free tier.

Usage::

    # point at a run directory (finds logs/test.log inside it)
    python -m utils.ai_triage results/run_20260605_144611

    # or point straight at a log file
    python -m utils.ai_triage results/run_20260605_144611/logs/test.log

    # pick provider/model ad-hoc (overrides .env)
    python -m utils.ai_triage <path> --provider gemini --model gemini-2.0-flash

Config (config/<domain>/.env, gitignored)::

    AI_PROVIDER=gemini            # gemini | groq | ollama
    AI_MODEL=gemini-2.0-flash
    GEMINI_API_KEY=...            # required for gemini
    # GROQ_API_KEY=...            # required for groq
    # OLLAMA_BASE_URL=http://localhost:11434

Provider-agnostic by design: each backend is one small ``_call_*`` function
talking REST over httpx (already a project dependency), so swapping to a paid
Claude/OpenAI backend later is just another function.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from config.settings import get_settings

# ---------------------------------------------------------------------------
# Project "playbook": the known failure signatures the model must classify by.
# This is what makes triage accurate for THIS app (a micro-frontend host) instead
# of generic guessing. Keep it in sync with how the tests log failures.
# ---------------------------------------------------------------------------
PLAYBOOK = """\
You are triaging automated UI/API test failures for the BlazeUp SA Dashboard - a
MICRO-FRONTEND (MFE) host. The sidebar and top bar ALWAYS render; each section's
content module is fetched dynamically and can fail independently.

Classify every failure into EXACTLY ONE category:

- deploy_mfe   : log says the MFE error panel ("Something went wrong" / "Failed
                 to fetch dynamically imported module") is visible. This is a
                 DEPLOY / infrastructure problem, NOT a test bug and NOT a code
                 bug in the test. Recommended action: report to the deploy/MFE
                 team; re-run after redeploy.
- flaky_slow   : "did not render within N ms" / timeout, but NO error panel was
                 seen. The page was still loading (staging cold loads are slow,
                 8-30s+). Recommended action: re-run; consider a larger timeout.
                 Not a real bug.
- test_or_ui_bug : a selector/marker that should exist was not found, or an
                 element-visibility assertion failed, with no MFE panel and no
                 timeout. Could be a stale locator OR a genuine UI regression.
                 Recommended action: a human should check the locator vs the UI.
- app_bug      : the page rendered but CONTENT is wrong (e.g. expected KPI/value
                 mismatch, wrong data). Recommended action: file an app bug.
- env_auth     : login/auth/setup failure, network/DNS, 4xx/5xx before the test
                 body. Recommended action: check credentials/env/target URL.
- unknown      : evidence is insufficient to decide confidently.

Rules:
- Decide ONLY from the evidence lines given. Do not invent log content.
- "tc_id" is the test-case id shown as the THIRD pipe-separated field of the log
  line (e.g. "TC-90000001"). Use the tc_id of the failing line. If a line has
  "--" (no tc), use "--".
- "confidence" is 0.0-1.0.
- "evidence" must quote the single most decisive log line (verbatim, trimmed).
- Be concise. One short sentence for "reason" and "recommendation".
"""

OUTPUT_CONTRACT = """\
Return ONLY a JSON object (no markdown fences, no prose) with this exact shape:

{
  "failures": [
    {
      "tc_id": "<the test-case id from the log line, e.g. TC-90000001, or -->",
      "item": "<page/test name, e.g. marketplace>",
      "category": "deploy_mfe|flaky_slow|test_or_ui_bug|app_bug|env_auth|unknown",
      "confidence": 0.0,
      "reason": "<one short sentence>",
      "evidence": "<the single most decisive log line, verbatim>",
      "recommendation": "<one short sentence>"
    }
  ],
  "summary": "<2-3 sentence overall verdict for the whole run>"
}
"""

# ---------------------------------------------------------------------------
# Log parsing — keep only what matters so the prompt stays small and cheap.
# ---------------------------------------------------------------------------

# "2026-06-05 14:47:57.078 | ERROR    | TC-12010201 | file.py:fn:60 | message"
_LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2}[ T][\d:.]+)\s*\|\s*"
    r"(?P<level>\w+)\s*\|\s*"
    r"(?P<tc>[\w-]+|--)\s*\|\s*"
    r"(?P<loc>[^|]+?)\s*\|\s*"
    r"(?P<msg>.*)$"
)

_FAIL_LEVELS = {"ERROR", "FAILED", "CRITICAL"}


@dataclass
class LogLine:
    raw: str
    level: str
    tc: str
    msg: str


@dataclass
class TriageInput:
    failed: bool
    context_block: str
    summary_block: str
    screenshots: list[str] = field(default_factory=list)


def _parse_lines(log_text: str) -> list[LogLine]:
    out: list[LogLine] = []
    for raw in log_text.splitlines():
        m = _LINE_RE.match(raw)
        if not m:
            continue
        out.append(LogLine(raw=raw.rstrip(), level=m["level"].upper(),
                           tc=m["tc"], msg=m["msg"].strip()))
    return out


def _extract_summary_block(log_text: str) -> str:
    """Return the trailing '# ===== TEST RUN SUMMARY ... =====' block, if any."""
    marker = "# ===== TEST RUN SUMMARY"
    idx = log_text.find(marker)
    return log_text[idx:].strip() if idx != -1 else ""


def build_triage_input(log_text: str, context_before: int = 4) -> TriageInput:
    """Filter the log down to failures + a few context lines before each.

    For every ERROR/FAILED line we keep the preceding ``context_before`` lines
    (which page, which URL was navigated, the wait_ready step) so the model can
    tell *why*, not just *that*, it failed. Screenshot paths are harvested from
    "Saved failure screenshot to ..." lines.
    """
    lines = _parse_lines(log_text)
    keep_idx: set[int] = set()
    screenshots: list[str] = []
    any_fail = False

    for i, ln in enumerate(lines):
        if "Saved failure screenshot to" in ln.msg:
            screenshots.append(ln.msg.split("to", 1)[-1].strip())
        if ln.level in _FAIL_LEVELS:
            any_fail = True
            for j in range(max(0, i - context_before), i + 1):
                keep_idx.add(j)

    block = "\n".join(lines[i].raw for i in sorted(keep_idx))
    return TriageInput(
        failed=any_fail,
        context_block=block,
        summary_block=_extract_summary_block(log_text),
        screenshots=screenshots,
    )


def build_prompt(ti: TriageInput) -> str:
    return (
        f"{PLAYBOOK}\n\n"
        f"--- FILTERED LOG (failures + context) ---\n{ti.context_block}\n\n"
        f"--- RUN SUMMARY ---\n{ti.summary_block or '(none)'}\n\n"
        f"{OUTPUT_CONTRACT}"
    )


# ---------------------------------------------------------------------------
# Providers — each returns the raw model text. All over httpx (no extra deps).
# ---------------------------------------------------------------------------

def _call_gemini(prompt: str, model: str, api_key: str, timeout: float = 60.0,
                 max_retries: int = 2) -> str:
    # Key goes in the x-goog-api-key HEADER, not the URL query string, so it
    # never leaks into error messages, tracebacks, or proxy/access logs.
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    )
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.0, "responseMimeType": "application/json"},
    }
    for attempt in range(max_retries + 1):
        resp = httpx.post(url, headers=headers, json=body, timeout=timeout)
        if resp.status_code == 429:
            quota_id, msg, retry_delay = _parse_gemini_429(resp)
            if attempt < max_retries:
                wait = retry_delay if retry_delay is not None else 20 * (attempt + 1)
                print(f"  Gemini 429 [{quota_id or 'rate limit'}]; retrying in {wait}s "
                      f"[{attempt + 1}/{max_retries}]...")
                time.sleep(wait)
                continue
            raise SystemExit(
                "Gemini returned 429 (quota/rate limit) after retries.\n"
                f"  which quota : {quota_id or 'unknown'}\n"
                f"  google says : {msg or '(no detail)'}\n"
                "  fixes:\n"
                "   - if quota id ends in 'PerDay'  -> daily free quota used up; wait until "
                "reset (Pacific midnight) or use another key/provider,\n"
                "   - if it ends in 'PerMinute'     -> wait ~60s and retry,\n"
                "   - try a different free model:    --model gemini-1.5-flash\n"
                "   - or switch provider:            --provider groq  /  --provider ollama\n"
                "   - check quota: https://aistudio.google.com/app/apikey"
            )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    raise SystemExit("Gemini call failed unexpectedly.")  # unreachable


def _parse_gemini_429(resp: httpx.Response) -> tuple[str | None, str | None, int | None]:
    """Pull (quota_id, message, retry_delay_seconds) out of a Gemini 429 body.

    Gemini's 429 JSON carries the decisive detail the bare status code hides:
    which quota was exceeded (per-minute vs per-day) and a suggested retryDelay.
    """
    quota_id = msg = None
    retry_delay: int | None = None
    try:
        err = resp.json().get("error", {})
        msg = err.get("message")
        for d in err.get("details", []):
            for v in d.get("violations", []):
                quota_id = v.get("quotaId") or quota_id
            rd = d.get("retryDelay")  # e.g. "17s"
            if isinstance(rd, str) and rd.endswith("s"):
                try:
                    retry_delay = int(float(rd[:-1])) + 1
                except ValueError:
                    pass
    except (json.JSONDecodeError, AttributeError):
        msg = resp.text[:300]
    return quota_id, msg, retry_delay


def _call_groq(prompt: str, model: str, api_key: str, timeout: float = 60.0) -> str:
    resp = httpx.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def _call_ollama(prompt: str, model: str, base_url: str, timeout: float = 120.0) -> str:
    resp = httpx.post(
        f"{base_url.rstrip('/')}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False, "format": "json",
              "options": {"temperature": 0.0}},
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def call_ai(prompt: str, *, provider: str, model: str, settings) -> str:
    """Dispatch to the configured provider. Raises a clear error if key missing."""
    if provider == "gemini":
        key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise SystemExit("GEMINI_API_KEY is not set. Add it to config/<domain>/.env "
                             "(get a free key at https://aistudio.google.com/apikey).")
        return _call_gemini(prompt, model, key)
    if provider == "groq":
        key = settings.groq_api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise SystemExit("GROQ_API_KEY is not set. Add it to config/<domain>/.env.")
        return _call_groq(prompt, model, key)
    if provider == "ollama":
        return _call_ollama(prompt, model, str(settings.ollama_base_url))
    raise SystemExit(f"Unknown AI_PROVIDER '{provider}'. Use gemini | groq | ollama.")


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

_CAT_EMOJI = {
    "deploy_mfe": "DEPLOY",
    "flaky_slow": "FLAKY",
    "test_or_ui_bug": "TEST/UI",
    "app_bug": "APP BUG",
    "env_auth": "ENV/AUTH",
    "unknown": "UNKNOWN",
}


def _coerce_json(text: str) -> dict:
    """Parse the model's reply, tolerating accidental ```json fences."""
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\n?|\n?```$", "", t).strip()
    return json.loads(t)


def render_markdown(result: dict, log_path: Path) -> str:
    rows = result.get("failures", [])
    lines = [
        "# AI Failure Triage",
        "",
        f"- Log: `{log_path}`",
        f"- Failures analysed: **{len(rows)}**",
        "",
        f"> {result.get('summary', '(no summary)')}",
        "",
        "| Test Case | Item | Category | Conf | Reason | Recommendation |",
        "|-----------|------|----------|------|--------|----------------|",
    ]
    for r in rows:
        cat = _CAT_EMOJI.get(r.get("category", "unknown"), r.get("category", "?"))
        lines.append(
            f"| {r.get('tc_id','--')} | {r.get('item','?')} | {cat} | "
            f"{r.get('confidence','?')} | {r.get('reason','')} | {r.get('recommendation','')} |"
        )
    lines += ["", "## Evidence", ""]
    for r in rows:
        lines.append(f"- **{r.get('tc_id','--')} / {r.get('item','?')}** — "
                     f"`{r.get('evidence','')}`")
    return "\n".join(lines) + "\n"


def _print_console(result: dict) -> None:
    print("\n=== AI Failure Triage ===")
    print(result.get("summary", "(no summary)"))
    print("-" * 60)
    for r in result.get("failures", []):
        print(f"  [{_CAT_EMOJI.get(r.get('category'), r.get('category','?'))}] "
              f"{r.get('tc_id','--')}  {r.get('item','?')}  (conf {r.get('confidence','?')})")
        print(f"      reason : {r.get('reason','')}")
        print(f"      action : {r.get('recommendation','')}")
    print("-" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _resolve_log_path(target: str) -> Path:
    p = Path(target)
    if p.is_dir():
        candidate = p / "logs" / "test.log"
        if not candidate.exists():
            raise SystemExit(f"No logs/test.log found under {p}")
        return candidate
    if not p.exists():
        raise SystemExit(f"Path not found: {p}")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI triage of a BlazeUp test run log.")
    parser.add_argument("target", help="run directory or path to test.log")
    parser.add_argument("--provider", default=None, help="override AI_PROVIDER")
    parser.add_argument("--model", default=None, help="override AI_MODEL")
    parser.add_argument("--print-prompt", action="store_true",
                        help="print the filtered prompt and exit (no API call)")
    args = parser.parse_args(argv)

    settings = get_settings()
    provider = args.provider or settings.ai_provider
    model = args.model or settings.ai_model

    log_path = _resolve_log_path(args.target)
    log_text = log_path.read_text(encoding="utf-8", errors="replace")

    ti = build_triage_input(log_text)
    if not ti.failed:
        print(f"No failures found in {log_path} — nothing to triage.")
        return 0

    prompt = build_prompt(ti)
    if args.print_prompt:
        print(prompt)
        return 0

    print(f"Triaging {log_path}\n  provider={provider} model={model} "
          f"(screenshots seen: {len(ti.screenshots)})")
    raw = call_ai(prompt, provider=provider, model=model, settings=settings)

    try:
        result = _coerce_json(raw)
    except json.JSONDecodeError:
        out = log_path.parent / "ai_triage_raw.txt"
        out.write_text(raw, encoding="utf-8")
        raise SystemExit(f"Model did not return valid JSON. Raw reply saved to {out}")

    md = render_markdown(result, log_path)
    out_md = log_path.parent.parent / "ai_triage.md"  # run_dir/ai_triage.md
    out_md.write_text(md, encoding="utf-8")
    _print_console(result)
    print(f"\nSaved: {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
