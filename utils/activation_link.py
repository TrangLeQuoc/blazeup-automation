"""Read the one-time activation token out of a partner invitation e-mail (opt-in test helper).

The backend never returns the token over HTTP (by design) — it only goes out in the e-mail,
as ``{PARTNER_PORTAL_BASE_URL}/activate#token=<43 chars>``. A test that needs it therefore
has to read the notification some other way. Sources are pluggable via
``settings.activation_link_source``:

* ``none``        — no source; ``get_activation_token`` returns ``None`` and the caller SKIPS.
* ``kafka-local`` — local stack: ``docker exec <container> rpk topic consume <topic> -o -1 -n 1``.
* ``cmd``         — ``settings.activation_link_cmd`` is run through the shell and must print the
                    latest notification/e-mail body (JSON or HTML) to stdout. This is the hook
                    for staging: wire it to a mailbox API / Mailosaur / a kubectl+rpk one-liner.

The token is a credential: it is never logged, only returned to the caller.
"""

import asyncio
import json
import re
import subprocess
from typing import Any

TOKEN_RE = re.compile(r"activate(?:#|%23)token=([A-Za-z0-9_-]+)")

_POLL_INTERVAL_S = 1.0


def extract_token(text: str) -> str | None:
    """Return the LAST activation token in ``text``, or None. Pure; the newest link wins."""
    matches = TOKEN_RE.findall(text or "")
    return matches[-1] if matches else None


def recipients_of(raw: str) -> list[str]:
    """Lower-cased ``recipients.to`` of a notification envelope; ``[]`` if it is not one."""
    try:
        body: Any = json.loads(raw)
    except (ValueError, TypeError):
        return []
    to = (
        ((body.get("payload") or {}).get("recipients") or {}).get("to")
        if isinstance(body, dict)
        else None
    )
    return [str(a).lower() for a in to] if isinstance(to, list) else []


def token_for(raw: str, email: str | None) -> str | None:
    """Token in ``raw`` if the message is addressed to ``email`` (any message when ``email`` is None).

    Guards against reading a stale message left by an earlier invite for someone else.
    """
    if email is not None:
        to = recipients_of(raw)
        if to and email.lower() not in to:
            return None
    return extract_token(raw)


def _run(argv: list[str] | str, *, shell: bool = False, timeout: float = 20.0) -> str:
    """Run a command and return stdout ('' on any failure) — a missing source must not raise."""
    try:
        done = subprocess.run(  # noqa: S603 — argv built from config, not user input
            argv, shell=shell, capture_output=True, text=True, timeout=timeout, check=False
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return done.stdout or ""


def _read_latest(settings) -> str:
    """Fetch the newest notification text from the configured source ('' when none)."""
    source = settings.activation_link_source
    if source == "kafka-local":
        return _run(
            [
                "docker",
                "exec",
                settings.activation_kafka_container,
                "rpk",
                "topic",
                "consume",
                settings.activation_kafka_topic,
                "-o",
                "-1",
                "-n",
                "1",
                "-f",
                "%v\\n",
            ]
        )
    if source == "cmd" and settings.activation_link_cmd:
        return _run(settings.activation_link_cmd, shell=True)  # noqa: S604 — operator-supplied
    return ""


def is_configured(settings) -> bool:
    """True when some source can supply a token."""
    s = settings.activation_link_source
    return s == "kafka-local" or (s == "cmd" and bool(settings.activation_link_cmd))


def skip_reason() -> str:
    """Why a token-dependent test skipped — shown verbatim in the report."""
    return (
        "no activation-link source configured (set ACTIVATION_LINK_SOURCE=kafka-local for a "
        "local stack, or ACTIVATION_LINK_SOURCE=cmd + ACTIVATION_LINK_CMD for a staging mailbox)"
    )


async def get_activation_token(
    settings, email: str | None = None, *, not_token: str | None = None, timeout_s: float = 20.0
) -> str | None:
    """Poll the source until a token for ``email`` shows up; None if unconfigured/timeout.

    ``not_token`` lets a caller wait for a NEWER link (after resend) instead of re-reading
    the previous one. Blocking subprocess calls run in a thread so the event loop stays free.
    """
    if not is_configured(settings):
        return None
    deadline = asyncio.get_event_loop().time() + timeout_s
    while True:
        raw = await asyncio.to_thread(_read_latest, settings)
        token = token_for(raw, email)
        if token and token != not_token:
            return token
        if asyncio.get_event_loop().time() >= deadline:
            return None
        await asyncio.sleep(_POLL_INTERVAL_S)
