"""make_win_intake: the win body must describe the SAME tenant the deal registered.

Found in review 2026-10-14: the default (random) profile ignored ``tenant_domain`` and
always generated a fresh label, while only the real-data profile honoured it. The BE takes
``dto.tenantDomain`` over the deal's own, so the winning tenant would be provisioned under
a domain nobody registered. The same profile also never sent ``adminPhoneNumber``, which
the win requires — the win would keep failing even after BUG-API-043 is fixed.
"""

import pytest

from utils import data_factory
from utils.data_factory import make_win_intake


@pytest.fixture(autouse=True)
def _random_profile(monkeypatch):
    # The bug lived in the DEFAULT profile; never let a local --real-data env leak in.
    monkeypatch.setattr(data_factory, "real_data_enabled", lambda: False)


def test_a_passed_tenant_domain_is_used_as_is():
    assert make_win_intake("plan-1", tenant_domain="acme-deal-01")["tenantDomain"] == (
        "acme-deal-01"
    )


def test_without_a_tenant_domain_each_call_gets_a_fresh_bare_label():
    a, b = make_win_intake("plan-1")["tenantDomain"], make_win_intake("plan-1")["tenantDomain"]
    assert a != b, "a second win must never collide with the tenant the first one created"
    assert "." not in a, "the BE refuses dotted domains — tenantDomain is a bare label"


def test_admin_phone_is_always_sent_with_an_iso_country_code():
    body = make_win_intake("plan-1")
    phone = body.get("adminPhoneNumber")
    assert phone and phone.get("number"), "the win requires adminPhoneNumber"
    assert phone["countryCode"] == body["country"], "countryCode is ISO alpha-2, like `country`"


def test_overrides_still_win():
    assert make_win_intake("plan-1", billingCycle="ANNUAL")["billingCycle"] == "ANNUAL"
