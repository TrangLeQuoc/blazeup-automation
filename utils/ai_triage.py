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
import contextlib
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
You are given DISTINCT failure signatures (deduplicated across the whole run), each
with an index and a representative log line. Classify ONLY these signatures.

Return ONLY a JSON object (no markdown fences, no prose) with this exact shape:

{
  "classifications": [
    {
      "index": <int — the signature's index, exactly as given>,
      "category": "deploy_mfe|flaky_slow|test_or_ui_bug|app_bug|env_auth|unknown",
      "reason": "<one short sentence>",
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

# Unknown (non-rule-classified) signatures are sent to the LLM in small BATCHES so
# each request stays well under provider payload limits (no HTTP 413), while ALL of
# them still get classified — this is what lets triage handle a run with many
# genuinely-distinct failures. A hard ceiling bounds cost on a pathological run; if
# it is hit, the dropped count is logged (never a silent cap).
_LLM_BATCH = 30
_MAX_LLM_SIGNATURES = 150
_MAX_EVIDENCE_CHARS = 300


@dataclass
class LogLine:
    raw: str
    level: str
    tc: str
    msg: str


@dataclass
class FailGroup:
    """A group of failing TCs that share one normalized failure signature."""

    signature: str
    evidence: str
    category: str = "unknown"
    reason: str = ""
    recommendation: str = ""
    tcs: list[str] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.tcs)


def _parse_lines(log_text: str) -> list[LogLine]:
    out: list[LogLine] = []
    for raw in log_text.splitlines():
        m = _LINE_RE.match(raw)
        if not m:
            continue
        out.append(
            LogLine(raw=raw.rstrip(), level=m["level"].upper(), tc=m["tc"], msg=m["msg"].strip())
        )
    return out


def _extract_summary_block(log_text: str) -> str:
    """Return the trailing '# ===== TEST RUN SUMMARY ... =====' block, if any."""
    marker = "# ===== TEST RUN SUMMARY"
    idx = log_text.find(marker)
    return log_text[idx:].strip() if idx != -1 else ""


# Normalize a message to a stable signature so failures with the same root cause
# collapse to one group (mongo ids / numbers / quoted values masked).
_ID_RE = re.compile(r"\b[0-9a-fA-F]{24}\b")
_QUOTED_RE = re.compile(r"(['\"]).*?\1")
_NUM_RE = re.compile(r"\d+")

# Deterministic rules for the common, unambiguous causes — these never need the LLM,
# so a run with hundreds of failures across a few known causes costs ZERO API calls.
_RULES: list[tuple[tuple[str, ...], str]] = [
    (
        ("502", "503", "504", "bad gateway", "upstream", "service unavailable", "econnrefused"),
        "env_auth",
    ),
    (("exceeded limit", "did not render", "timed out", "timeout"), "flaky_slow"),
    (("dynamically imported module", "something went wrong"), "deploy_mfe"),
    # BE-defect signatures the be_gap tests emit — classify deterministically as
    # app_bug so a mis-firing LLM can't relabel them env_auth (e.g. a ghost FK
    # accepted with 2xx reads like "status 201" but is a real backend bug).
    (
        (
            "confirm with be",
            "confirm be",
            "must not dup",
            "must be idempotent",
            "must stamp",
            "not stamped",
            "verified absent",
            "should reject",
            "must reject",
            "should be rejected",
        ),
        "app_bug",
    ),
]


def _signature(msg: str) -> str:
    """Reduce a failure message to a stable signature so same-cause failures collapse.

    Keys on the decisive error (the part after ``--``/``AssertionError:``) rather than
    the step name + timing, so e.g. every "got 502" setup failure — regardless of which
    step hit it — becomes ONE group. Ids / numbers / quoted values are masked.
    """
    core = msg.split(" -- ", 1)[-1]
    if "AssertionError:" in core:
        core = core.split("AssertionError:", 1)[-1]
    s = _ID_RE.sub("<id>", core.strip())
    s = _QUOTED_RE.sub("'<v>'", s)
    s = _NUM_RE.sub("<n>", s)
    return s.lower()[:120]


def _rule_category(text: str) -> str:
    """Best-effort deterministic category; ``unknown`` falls through to the LLM."""
    t = text.lower()
    for needles, cat in _RULES:
        if any(n in t for n in needles):
            return cat
    if "assert" in t or "expected" in t or " got " in t:
        return "test_or_ui_bug"
    return "unknown"


def collect_fail_groups(log_text: str) -> list[FailGroup]:
    """Group failing TCs by a normalized failure signature (dedup), rule-classify each.

    A TC's decisive evidence is its first ERROR/CRITICAL line (falling back to the
    FAILED verdict). TCs that fail for the same reason collapse into one group, so the
    LLM payload is proportional to the number of DISTINCT causes — not the total
    failure count. This is what makes triage scale to 1000+ TC runs.
    """
    lines = _parse_lines(log_text)
    evidence_by_tc: dict[str, str] = {}
    verdict_by_tc: dict[str, str] = {}
    order: list[str] = []
    for ln in lines:
        if ln.level in {"ERROR", "CRITICAL"} and ln.msg and ln.tc not in evidence_by_tc:
            evidence_by_tc[ln.tc] = ln.msg
        if ln.level == "FAILED":
            verdict_by_tc.setdefault(ln.tc, ln.msg)
            if ln.tc not in order:
                order.append(ln.tc)

    groups: dict[str, FailGroup] = {}
    for tc in order:
        evidence = evidence_by_tc.get(tc) or verdict_by_tc.get(tc, "(no evidence)")
        sig = _signature(evidence)
        g = groups.get(sig)
        if g is None:
            groups[sig] = FailGroup(
                signature=sig, evidence=evidence, category=_rule_category(evidence), tcs=[tc]
            )
        else:
            g.tcs.append(tc)
    return list(groups.values())


def collect_passed_tcs(log_text: str) -> set[int]:
    """Return the numeric ids of every TC that PASSED this run (from the log verdicts).

    Feeds the Bug Tracker's RESOLVED report: an open bug whose TC passed is no longer
    reproducing. A PASSED verdict is authoritative — a transient ERROR line inside a
    passing test never produces a FAILED verdict, so pass/fail sets stay disjoint.
    """
    passed: set[int] = set()
    for ln in _parse_lines(log_text):
        if ln.level == "PASSED":
            m = re.search(r"\d+", ln.tc or "")
            if m:
                passed.add(int(m.group()))
    return passed


def _group_prompt(unknown: list[FailGroup]) -> str:
    """Compact prompt: classify ONLY the distinct unknown signatures (index + one line each)."""
    listing = "\n".join(f"[{i}] {g.evidence[:_MAX_EVIDENCE_CHARS]}" for i, g in enumerate(unknown))
    return (
        f"{PLAYBOOK}\n\n"
        f"--- DISTINCT FAILURE SIGNATURES TO CLASSIFY ---\n{listing}\n\n"
        f"{OUTPUT_CONTRACT}"
    )


def classify_unknown_groups(groups: list[FailGroup], *, provider: str, model: str, settings) -> str:
    """Classify the unknown-category groups via the LLM in small batches.

    Each batch is one bounded API call (no 413); ALL unknowns up to
    ``_MAX_LLM_SIGNATURES`` get classified. A batch that errors is skipped (its groups
    stay ``unknown``) so one bad reply never aborts the rest. Returns a run summary;
    any signatures dropped by the hard ceiling are reported (never a silent cap).
    """
    all_unknown = [g for g in groups if g.category == "unknown"]
    if not all_unknown:
        return "All failures matched known causes (rule-classified) — no LLM call needed."

    unknown = all_unknown[:_MAX_LLM_SIGNATURES]
    dropped = len(all_unknown) - len(unknown)
    summaries: list[str] = []
    for start in range(0, len(unknown), _LLM_BATCH):
        batch = unknown[start : start + _LLM_BATCH]  # indices in the prompt are 0..len(batch)-1
        try:
            result = _coerce_json(
                call_ai(_group_prompt(batch), provider=provider, model=model, settings=settings)
            )
        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            print(f"  triage batch {start // _LLM_BATCH + 1} skipped ({type(exc).__name__})")
            continue
        for c in result.get("classifications", []):
            i = c.get("index")
            if isinstance(i, int) and 0 <= i < len(batch):
                g = batch[i]
                g.category = c.get("category", "unknown")
                g.reason = c.get("reason", "")
                g.recommendation = c.get("recommendation", "")
        if result.get("summary"):
            summaries.append(result["summary"])

    summary = " ".join(summaries) or "Classified distinct failure causes via the LLM."
    if dropped:
        summary += (
            f" NOTE: {dropped} additional distinct signature(s) exceeded the "
            f"{_MAX_LLM_SIGNATURES}-signature ceiling and were left UNKNOWN — see test.log."
        )
    return summary


# ---------------------------------------------------------------------------
# Providers — each returns the raw model text. All over httpx (no extra deps).
# ---------------------------------------------------------------------------


def _call_gemini(
    prompt: str, model: str, api_key: str, timeout: float = 60.0, max_retries: int = 2
) -> str:
    # Key goes in the x-goog-api-key HEADER, not the URL query string, so it
    # never leaks into error messages, tracebacks, or proxy/access logs.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
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
                print(
                    f"  Gemini 429 [{quota_id or 'rate limit'}]; retrying in {wait}s "
                    f"[{attempt + 1}/{max_retries}]..."
                )
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
                with contextlib.suppress(ValueError):
                    retry_delay = int(float(rd[:-1])) + 1
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
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.0},
        },
        timeout=timeout,
    )
    resp.raise_for_status()
    return resp.json()["response"]


def call_ai(prompt: str, *, provider: str, model: str, settings) -> str:
    """Dispatch to the configured provider. Raises a clear error if key missing."""
    if provider == "gemini":
        key = (settings.gemini_api_key or os.getenv("GEMINI_API_KEY") or "").strip()
        if not key:
            raise SystemExit(
                "GEMINI_API_KEY is not set. Add it to config/<domain>/.env "
                "(get a free key at https://aistudio.google.com/apikey)."
            )
        return _call_gemini(prompt, model, key)
    if provider == "groq":
        # .strip() guards against a trailing newline/space in the key (a common
        # cause of httpx "Illegal header value" when the key comes from a secret).
        key = (settings.groq_api_key or os.getenv("GROQ_API_KEY") or "").strip()
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


def _sample_tcs(g: FailGroup) -> str:
    """List EVERY failing TC id in the group.

    A failure report must never hide which tests failed behind a "+N more"
    truncation — the reader needs the full list to know exactly what to check.
    """
    return ", ".join(g.tcs)


def render_markdown(groups: list[FailGroup], log_path: Path, summary: str) -> str:
    groups = sorted(groups, key=lambda g: g.count, reverse=True)
    total = sum(g.count for g in groups)
    lines = [
        "# AI Failure Triage",
        "",
        f"- Log: `{log_path}`",
        f"- Failures: **{total}** across **{len(groups)}** distinct cause(s)",
        "",
        f"> {summary or '(no summary)'}",
        "",
        "| Category | Count | Sample TCs | Reason | Recommendation |",
        "|----------|-------|-----------|--------|----------------|",
    ]
    for g in groups:
        cat = _CAT_EMOJI.get(g.category, g.category)
        lines.append(f"| {cat} | {g.count} | {_sample_tcs(g)} | {g.reason} | {g.recommendation} |")
    lines += ["", "## Evidence (one representative per cause)", ""]
    for g in groups:
        cat = _CAT_EMOJI.get(g.category, g.category)
        lines.append(f"- **{cat}** ({g.count}× — {_sample_tcs(g)}) — `{g.evidence[:200]}`")
    return "\n".join(lines) + "\n"


def _print_console(groups: list[FailGroup], summary: str) -> None:
    groups = sorted(groups, key=lambda g: g.count, reverse=True)
    total = sum(g.count for g in groups)
    print("\n=== AI Failure Triage ===")
    print(f"{total} failure(s) → {len(groups)} distinct cause(s)")
    print(summary or "(no summary)")
    print("-" * 60)
    for g in groups:
        print(f"  [{_CAT_EMOJI.get(g.category, g.category)}] {g.count}×  {_sample_tcs(g)}")
        print(f"      reason : {g.reason or '(rule-classified)'}")
        if g.recommendation:
            print(f"      action : {g.recommendation}")
        print(f"      example: {g.evidence[:120]}")
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
    # The reconciliation block prints emojis (✅ 🔵 ⚠ 🆕); the Windows console's
    # cp1252 default would crash on them, so force UTF-8 output when possible.
    with contextlib.suppress(Exception):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="AI triage of a BlazeUp test run log.")
    parser.add_argument("target", help="run directory or path to test.log")
    parser.add_argument("--provider", default=None, help="override AI_PROVIDER")
    parser.add_argument("--model", default=None, help="override AI_MODEL")
    parser.add_argument(
        "--print-prompt",
        action="store_true",
        help="print the filtered prompt and exit (no API call)",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    provider = args.provider or settings.ai_provider
    model = args.model or settings.ai_model

    log_path = _resolve_log_path(args.target)
    log_text = log_path.read_text(encoding="utf-8", errors="replace")

    groups = collect_fail_groups(log_text)
    passed_tcs = collect_passed_tcs(log_text)
    if not groups:
        # No failures — but a fully-green run can still RESOLVE open bugs (every
        # be_gap test that a BE fix turned green lands here). Report those and stop.
        from utils.bug_tracker import reconcile as reconcile_bugs
        from utils.bug_tracker import render as render_bugs

        recon = reconcile_bugs([], passed_tc_ids=passed_tcs)
        print(f"No failures found in {log_path} — nothing to triage.")
        block = render_bugs(recon)
        print(block)
        if recon.resolved:
            out_md = log_path.parent.parent / "ai_triage.md"
            out_md.write_text(
                "# AI Failure Triage\n\n(no failures)\n" + block + "\n", encoding="utf-8"
            )
            print(f"\nSaved: {out_md}")
        return 0

    total = sum(g.count for g in groups)
    unknown = [g for g in groups if g.category == "unknown"]

    if args.print_prompt:
        print(
            _group_prompt(unknown)
            if unknown
            else "(all failure groups were rule-classified — no LLM prompt needed)"
        )
        return 0

    print(
        f"Triaging {log_path}\n  {total} failure(s) → {len(groups)} distinct cause(s); "
        f"{len(unknown)} need the LLM (provider={provider} model={model})"
    )
    try:
        summary = classify_unknown_groups(groups, provider=provider, model=model, settings=settings)
    except json.JSONDecodeError as exc:
        out = log_path.parent / "ai_triage_raw.txt"
        out.write_text(str(exc), encoding="utf-8")
        raise SystemExit(f"Model did not return valid JSON. Detail saved to {out}") from exc

    # Reconcile real backend defects (category app_bug) against the Bug Tracker —
    # deterministic (keyed by Test Case ID). New bugs are appended on local runs;
    # on CI it is propose-only (report, no file change).
    from utils.bug_tracker import reconcile as reconcile_bugs
    from utils.bug_tracker import render as render_bugs

    recon = reconcile_bugs(groups, passed_tc_ids=passed_tcs)
    bug_block = render_bugs(recon)

    md = render_markdown(groups, log_path, summary) + "\n" + bug_block + "\n"
    out_md = log_path.parent.parent / "ai_triage.md"  # run_dir/ai_triage.md
    out_md.write_text(md, encoding="utf-8")
    _print_console(groups, summary)
    print(bug_block)
    print(f"\nSaved: {out_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
