"""Test data factories — generate unique, identifiable payloads with Faker.

Why factories instead of hard-coded data:
  * Uniqueness  — uniqueness-sensitive fields (email, domain, prospect name) carry a
    uuid ``_token``, so records never collide on "already exists" across runs OR in
    parallel (-n auto). (Faker's ``.unique`` only dedupes within one process, so it
    repeats across separate runs — avoid it for anything the BE persists.)
  * Identifiable — names/emails carry the ``QA-AUTO`` prefix, so automation data
    is easy to spot and bulk-clean on shared environments.
  * Overridable — pass kwargs to pin any field you want to assert on, e.g.
    ``make_user(email="fixed@x.com")``.

Usage::

    from utils.data_factory import make_user
    payload = make_user()                      # all random + tagged
    payload = make_user(department="Finance")  # override one field

These return plain dicts. ADJUST the fields to match each real API contract when
the endpoints are finalized — the structure here is a sensible starting point,
not a guarantee of the backend schema.
"""

import uuid
from typing import Any

from faker import Faker

# Module-level generator. For cross-run-unique values use ``_token`` (below), not
# ``_fake.unique`` — the latter only dedupes within a single process.
_fake = Faker()

# Prefix stamped onto human-readable fields so QA automation data is easy to
# find and clean up (e.g. filter tenants whose name starts with "QA-AUTO").
QA_AUTO_PREFIX = "QA-AUTO"


def tag(text: str) -> str:
    """Prefix a human-readable label so it's recognizable as automation data."""
    return f"{QA_AUTO_PREFIX} {text}"


def valid_phone() -> str:
    """Return a libphonenumber-valid E.164 phone number.

    The BE validates phone numbers strictly. A random ``"+1"+msisdn`` often yields
    an invalid area code → flaky 400 ("phone must be a valid phone number"). Phone
    is not a uniqueness key, so a known-good constant is the safe, deterministic
    choice across all factories.
    """
    return "+14155552671"


def _token(n: int = 12) -> str:
    """Short high-entropy token that is unique ACROSS runs (uuid-based, not pool-based).

    This is the safe uniqueness primitive for anything the BE persists and rejects on
    repeat: unlike Faker's ``.unique`` (in-memory, per-process, small pool → repeats
    across runs) a uuid slice never collides between runs, and never raises
    ``UniquenessException`` when a pool is exhausted.
    """
    return uuid.uuid4().hex[:n]


def unique_email(domain: str = "mailinator.com") -> str:
    """Return an email unique ACROSS runs (not just within one process), tagged for cleanup.

    Faker's ``.unique`` only dedupes within a single process, and ``user_name()`` draws
    from a small pool — so across separate runs the SAME address recurs. Because created
    records persist on staging, the BE then rejects the re-used address with 400
    "already exists" (this is what flaked partner/deal setups). A short uuid token makes
    the local-part globally unique; the readable username keeps it identifiable and '+'
    tagging keeps it one real inbox.
    """
    return f"qa.auto+{_fake.user_name()}-{_token()}@{domain}"


def unique_domain(tld: str = "com") -> str:
    """Return a syntactically-valid domain unique ACROSS runs (for tenantDomain etc.).

    ``fake.unique.domain_name()`` repeats across runs (same reason as ``unique_email``);
    a persisted tenant domain then collides. The ``qa-auto-`` label keeps it identifiable
    and bulk-cleanable, and the uuid token guarantees global uniqueness.
    """
    return f"qa-auto-{_token(10)}.{tld}"


def make_user(**overrides: Any) -> dict[str, Any]:
    """Build a user/employee creation payload."""
    data: dict[str, Any] = {
        "first_name": _fake.first_name(),
        "last_name": _fake.last_name(),
        "email": unique_email(),
        "phone": valid_phone(),
        "department": _fake.job(),
        "title": _fake.job(),
    }
    data.update(overrides)
    return data


def make_tenant(**overrides: Any) -> dict[str, Any]:
    """Build a tenant/organization creation payload."""
    data: dict[str, Any] = {
        "name": tag(_fake.company()),
        "domain": unique_domain(),
        "admin_email": unique_email(),
        "country": _fake.country_code(),
    }
    data.update(overrides)
    return data


def make_partner(**overrides: Any) -> dict[str, Any]:
    """Build a partner-creation payload matching ``CreatePartnerDto`` (sa-partners-api).

    Required by the API: ``name``, ``email``, ``type`` (one of
    channel / referral / msp / system_integrator). The rest are optional but
    populated so the created record is realistic. Pass overrides to vary fields,
    e.g. ``make_partner(type="referral")``.
    """
    data: dict[str, Any] = {
        "name": tag(_fake.company()),
        "email": unique_email(),
        "type": "channel",
        "phone": valid_phone(),
        "website": _fake.url(),
    }
    data.update(overrides)
    return data


def make_partner_user(partner_id: str, **overrides: Any) -> dict[str, Any]:
    """Build a partner-portal user invite payload matching ``InvitePartnerUserDto``.

    Required by the API: ``partnerId``, ``email``, ``firstName``, ``lastName``.
    ``role`` ∈ admin / sales / finance / viewer (defaults to admin).
    """
    data: dict[str, Any] = {
        "partnerId": partner_id,
        "email": unique_email(),
        "firstName": _fake.first_name(),
        "lastName": _fake.last_name(),
        "role": "admin",
    }
    data.update(overrides)
    return data


def make_prospect(**overrides: Any) -> dict[str, Any]:
    """Build a UNIQUE prospect identity (``prospectName`` + ``prospectEmail``).

    Deal-conflict detection keys on the prospect identity, so the name MUST be
    unique per test. A plain ``fake.company()`` is NOT unique — two conflict tests
    running in parallel (``-n auto``) can generate the same name and contaminate
    each other (a deal in test A flags against a deal in test B). A uuid ``_token``
    guarantees no repeat within OR across runs (``fake.unique`` only dedupes within
    one process, so it repeats across runs — see ``_token``).

    Reuse the SAME returned dict for both partners in a conflict test to create
    the intended same-prospect collision (the shared token makes both names equal)::

        prospect = make_prospect()
        await client.register_deal(make_deal(p1, plan, **prospect))
        await client.register_deal(make_deal(p2, plan, **prospect))  # flagged
    """
    data: dict[str, Any] = {
        "prospectName": tag(f"{_fake.company()} Prospect {_token(8)}"),
        "prospectEmail": unique_email(),
    }
    data.update(overrides)
    return data


def make_territory(partner_id: str, **overrides: Any) -> dict[str, Any]:
    """Build a territory-assignment payload matching ``CreateTerritoryDto`` (sa-partners-api).

    Required by the API: ``partnerId``, ``label``, ``countries`` (ISO 3166-1 alpha-2).
    ``exclusivityType`` ∈ exclusive / preferred / open (defaults ``preferred`` so the
    factory does not trigger cross-partner exclusive conflicts by default). Pass
    ``exclusivityType="exclusive"`` + a specific ``countries`` to test conflicts.
    """
    data: dict[str, Any] = {
        "partnerId": partner_id,
        "label": tag(f"{_fake.last_name()} Territory"),
        "countries": ["US"],
        "verticals": ["technology"],
        "exclusivityType": "preferred",
        "exclusivityStartDate": "2026-01-01",
        "exclusivityEndDate": "2026-12-31",
        "notes": tag(_fake.sentence()),
    }
    data.update(overrides)
    return data


def make_deal(partner_id: str, plan_id: str, **overrides: Any) -> dict[str, Any]:
    """Build a deal-registration payload matching ``CreateDealDto`` (sa-partners-api).

    Required by the API: ``dealType`` (referral / reseller / co_sell), ``tenantDomain``,
    ``prospectName``, ``prospectCountry``, ``estimatedAcvCents``, ``numberOfEmployee``,
    ``billingCycle`` (monthly / annual), ``expectedCloseDate``, plus ``planId``
    (a published billing plan; or pass an inline ``billingPlan``).
    """
    data: dict[str, Any] = {
        "partnerId": partner_id,
        "planId": plan_id,
        "dealType": "referral",
        "tenantDomain": unique_domain(),
        "prospectName": tag(f"{_fake.company()} Opportunity {_token(8)}"),
        "prospectEmail": unique_email(),
        "prospectPhone": valid_phone(),
        "prospectCountry": "US",
        "estimatedAcvCents": _fake.random_int(min=1_000_00, max=5_000_000_00),
        "currency": "USD",  # required by CreateDealDto (ISO 4217) — ACV/plan-budget currency
        "numberOfEmployee": _fake.random_int(min=10, max=5000),
        "billingCycle": "annual",
        "expectedCloseDate": "2026-12-31",
        "notes": tag(_fake.sentence()),
    }
    data.update(overrides)
    return data
