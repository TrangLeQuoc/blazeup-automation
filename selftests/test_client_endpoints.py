"""Every API-client method must still hit the endpoint it hit before.

Why this exists: the partner-portal paths used to be written out in four test modules.
Moving them into `PartnerPortalClient` is a mechanical rewrite of ~30 call sites, and a
mechanical rewrite's failure mode is a typo in a path — which no amount of local linting
catches, and which only shows up as a 404 against a live backend.

So the expected paths below are the LEGACY LITERALS, copied from the call sites as they
were before the move. They are deliberately duplicated here rather than imported from
the client: importing would make the test agree with any typo. If the client and this
list disagree, one of them is wrong.

If the BACKEND genuinely moves an endpoint, this test goes red on purpose — update the
client and this list together, so the change is explicit and reviewed instead of silent.

No network: `request()` is stubbed, so the client is exercised without a backend.
"""

import asyncio

import pytest

from api_clients.blazeup.admin.partner.sa_deals_client import SaDealsClient
from api_clients.blazeup.partner.partner_portal_client import PartnerPortalClient

# Prefixes as the tests used to spell them, before PartnerPortalClient existed.
PORTAL = "/sa-partners-api/v1/partner/portal"
AUTH = "/sa-partners-api/v1/partner/auth"
SA_DEALS = "/sa-partners-api/v1/sa/deals"


def _call(client_cls, method: str, *args, **kwargs) -> dict:
    """Invoke one client method with the HTTP layer stubbed; return what it would send.

    ``__new__`` without ``__init__`` on purpose: these methods only build a path and
    delegate to ``self.request``, so no transport is needed. Constructing the real
    ``httpx.AsyncClient`` for each of the 30-odd cases cost ~9 s for nothing. If a method
    ever needs more state this raises AttributeError — loud, which is what we want.
    """
    client = client_cls.__new__(client_cls)
    seen: dict = {}

    async def fake_request(verb: str, endpoint: str, **kw):
        seen.update(verb=verb, endpoint=endpoint, kwargs=kw)
        return None  # methods under test must not touch the response

    client.request = fake_request  # type: ignore[method-assign]
    asyncio.run(getattr(client, method)(*args, **kwargs))
    assert seen, f"{client_cls.__name__}.{method} sent no request at all"
    return seen


# (client class, method, args, kwargs, expected verb, expected endpoint)
CASES = [
    (PartnerPortalClient, "get_profile", (), {}, "GET", f"{PORTAL}/profile"),
    (PartnerPortalClient, "get_dashboard", (), {}, "GET", f"{PORTAL}/dashboard"),
    (
        PartnerPortalClient,
        "get_commissions_summary",
        (),
        {},
        "GET",
        f"{PORTAL}/commissions/summary",
    ),
    (PartnerPortalClient, "get_territories", (), {}, "GET", f"{PORTAL}/territories"),
    (PartnerPortalClient, "get_rates", (), {}, "GET", f"{PORTAL}/rates"),
    (PartnerPortalClient, "get_certifications", (), {}, "GET", f"{PORTAL}/certifications"),
    (PartnerPortalClient, "check_domain", ("acme",), {}, "GET", f"{PORTAL}/check-domain"),
    (PartnerPortalClient, "register_deal", ({"a": 1},), {}, "POST", f"{PORTAL}/deals"),
    (PartnerPortalClient, "list_deals", (), {}, "GET", f"{PORTAL}/deals"),
    (PartnerPortalClient, "get_deal", ("dealid1",), {}, "GET", f"{PORTAL}/deals/dealid1"),
    (PartnerPortalClient, "me", (), {}, "GET", f"{AUTH}/me"),
    (PartnerPortalClient, "login", ("e@x.com", "pw"), {}, "POST", f"{AUTH}/login"),
    (PartnerPortalClient, "refresh", ("tok",), {}, "POST", f"{AUTH}/refresh"),
    (PartnerPortalClient, "logout", (), {}, "POST", f"{AUTH}/logout"),
    (
        PartnerPortalClient,
        "change_password",
        ("old", "new"),
        {},
        "POST",
        f"{AUTH}/change-password",
    ),
    (
        SaDealsClient,
        "raw_update_deal",
        ("dealid1", {"notes": "x"}),
        {},
        "PATCH",
        f"{SA_DEALS}/dealid1",
    ),
]


@pytest.mark.parametrize(
    ("cls", "method", "args", "kwargs", "verb", "endpoint"),
    CASES,
    ids=[f"{c.__name__}.{m}" for c, m, *_ in CASES],
)
def test_method_hits_the_expected_endpoint(cls, method, args, kwargs, verb, endpoint):
    sent = _call(cls, method, *args, **kwargs)
    assert sent["endpoint"] == endpoint, (
        f"{cls.__name__}.{method} sends {sent['endpoint']!r}, expected {endpoint!r}"
    )
    assert sent["verb"] == verb, f"{cls.__name__}.{method} uses {sent['verb']}, expected {verb}"


# ── Payload / query shape for the methods that build one ─────────────────────
# These used to be written at the call site, so a wrong key here would silently change
# the request the test makes.


def test_check_domain_passes_the_label_as_a_query_param():
    sent = _call(PartnerPortalClient, "check_domain", "acme")
    assert sent["kwargs"].get("params") == {"domain": "acme"}


def test_login_body_matches_partner_login_dto():
    sent = _call(PartnerPortalClient, "login", "e@x.com", "pw")
    assert sent["kwargs"].get("json") == {"email": "e@x.com", "password": "pw"}


def test_refresh_body_uses_refresh_token_key():
    sent = _call(PartnerPortalClient, "refresh", "tok")
    assert sent["kwargs"].get("json") == {"refreshToken": "tok"}


def test_change_password_body_uses_current_and_new_keys():
    sent = _call(PartnerPortalClient, "change_password", "old", "new")
    assert sent["kwargs"].get("json") == {"currentPassword": "old", "newPassword": "new"}


def test_logout_sends_an_empty_json_body():
    """The BE rejects a bodyless POST here — the empty object is required."""
    sent = _call(PartnerPortalClient, "logout")
    assert sent["kwargs"].get("json") == {}


def test_auth_me_path_constant_matches_the_method():
    """The constant exists for a foreign client (SA token → 401) — it must not drift."""
    sent = _call(PartnerPortalClient, "me")
    assert sent["endpoint"] == PartnerPortalClient.AUTH_ME_PATH, "the constant drifted from me()"
    assert sent["endpoint"] == f"{AUTH}/me", "both drifted from the legacy path"


# ── Default expected_status per method ───────────────────────────────────────
# A method whose default is wider than the call site used to be would let a wrong status
# pass silently.


@pytest.mark.parametrize(
    ("method", "args", "expected"),
    [
        ("get_profile", (), 200),
        ("get_dashboard", (), 200),
        ("list_deals", (), 200),
        ("get_deal", ("d1",), 200),
        ("register_deal", ({},), (200, 201)),
        ("login", ("e", "p"), (200, 201)),
        ("refresh", ("t",), 200),
        ("logout", (), (200, 204)),
        ("change_password", ("a", "b"), (200, 204)),
    ],
)
def test_default_expected_status(method, args, expected):
    sent = _call(PartnerPortalClient, method, *args)
    assert sent["kwargs"].get("expected_status") == expected
