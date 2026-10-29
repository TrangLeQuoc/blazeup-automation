"""Pure parsing of the activation-link helper (no docker, no network).

The helper reads a one-time token out of a notification envelope. What matters: the newest
link wins, a message addressed to someone else is NOT used (a stale mail must never activate
the wrong invitee), and an unconfigured source yields None so token TCs skip instead of fail.
"""

import asyncio
import json
from types import SimpleNamespace

from utils.activation_link import extract_token, get_activation_token, is_configured, token_for

_TOK = "A" * 43


def _env(to: str, token: str = _TOK) -> str:
    return json.dumps(
        {
            "payload": {
                "recipients": {"to": [to]},
                "data": {"bodyHtml": f'x/activate#token={token}"'},
            }
        }
    )


def test_extract_token_takes_the_last_link() -> None:
    assert extract_token(f"a activate#token=OLD_1 b activate#token={_TOK}") == _TOK


def test_extract_token_none_when_absent() -> None:
    assert extract_token("no link here") is None
    assert extract_token("") is None


def test_token_for_ignores_a_message_for_another_recipient() -> None:
    assert token_for(_env("Other@x.test"), "me@x.test") is None
    assert token_for(_env("Me@x.test"), "me@X.test") == _TOK


def test_unconfigured_source_returns_none() -> None:
    s = SimpleNamespace(activation_link_source="none", activation_link_cmd=None)
    assert is_configured(s) is False
    assert asyncio.run(get_activation_token(s, "me@x.test", timeout_s=0.1)) is None
    cmd_no_command = SimpleNamespace(activation_link_source="cmd", activation_link_cmd=None)
    assert is_configured(cmd_no_command) is False
