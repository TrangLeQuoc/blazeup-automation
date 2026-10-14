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

import os
import uuid
from functools import lru_cache
from pathlib import Path
from typing import Any

from faker import Faker

# Module-level generator. For cross-run-unique values use ``_token`` (below), not
# ``_fake.unique`` — the latter only dedupes within a single process.
_fake = Faker()

# ── Real-data profile ─────────────────────────────────────────────────────────
# The runner's REAL_TEST_DATA flag (or --real-data) exports TEST_DATA_PROFILE=real;
# the factories then build payloads from config/blazeup/test_data.yaml (a real person,
# a real-looking company) instead of Faker. Uniqueness is NOT given up: every record
# still carries a run token (plus-addressed email, suffixed name/domain), because the
# BE rejects a repeated partner email / own-open prospect name and flags a repeated
# prospect+country as a conflict. Default is random — CI never sees personal data.
TEST_DATA_PROFILE_ENV = "TEST_DATA_PROFILE"
_REAL_DATA_FILE = Path(__file__).resolve().parents[1] / "config" / "blazeup" / "test_data.yaml"


def real_data_enabled() -> bool:
    """True when the run asked for real data (runner flag REAL_TEST_DATA / --real-data)."""
    return os.environ.get(TEST_DATA_PROFILE_ENV, "").strip().lower() == "real"


@lru_cache(maxsize=1)
def _real() -> dict[str, Any]:
    """The parsed test_data.yaml — loaded once, only when real data is enabled."""
    import yaml

    if not _REAL_DATA_FILE.exists():
        raise RuntimeError(
            f"REAL_TEST_DATA is on but {_REAL_DATA_FILE} does not exist — copy "
            "config/blazeup/test_data.example.yaml to test_data.yaml and fill it in, "
            "or run without --real-data."
        )
    data = yaml.safe_load(_REAL_DATA_FILE.read_text(encoding="utf-8")) or {}
    for section, key in (("contact", "email"), ("partner", "name"), ("deal", "company")):
        if not (data.get(section) or {}).get(key):
            raise RuntimeError(f"{_REAL_DATA_FILE.name}: `{section}.{key}` is required")
    return data


def _plus(email: str, label: str) -> str:
    """you@co.com -> you+<label>@co.com: unique per record, same real inbox."""
    local, _, domain = email.partition("@")
    return f"{local.split('+', 1)[0]}+{label}@{domain}"


def _real_phone() -> dict[str, str]:
    c = _real()["contact"]
    return {"number": str(c.get("phone") or "0987654321"), "countryCode": c.get("country", "VN")}


def contact_full_name() -> str:
    """Primary-contact full name for the register wizard (real person or a QA label)."""
    if real_data_enabled():
        c = _real()["contact"]
        return f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
    return "QA-AUTO Contact"


def contact_country_name() -> str | None:
    """Country as the wizard's dropdown spells it (real profile), or None = pick the first."""
    return _real()["contact"].get("country_name") if real_data_enabled() else None


def company_name(label: str) -> str:
    """A unique PROSPECT company name: '<deal.company> <token>' or 'QA-AUTO <label> <token>'."""
    if real_data_enabled():
        return f"{_real()['deal']['company']} {_token(6)}"
    return f"QA-AUTO {label} {_token(12)}"


def partner_name(label: str) -> str:
    """A unique PARTNER organisation name: '<partner.name> <token>' or 'QA-AUTO <label> <token>'."""
    if real_data_enabled():
        return f"{_real()['partner']['name']} {_token(6)}"
    return f"QA-AUTO {label} {_token(12)}"


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


def phone_detail(country_code: str = "US") -> dict[str, str]:
    """Return a phone as the nested ``PhoneDetail`` object the BE now requires.

    sa-partners-api changed its phone fields (CreatePartnerDto.phone,
    CreateDealDto.prospectPhone, PartnerContactDto.phone) from a flat E.164 string
    to a ``{"number", "countryCode"}`` object; a plain string now 400s with
    "nested property phone must be either object or array". ``number`` is the local
    subscriber number, ``countryCode`` an ISO 3166-1 alpha-2 code — 4155552671 / US
    is the known-good San Francisco number matching :func:`valid_phone`.
    """
    return {"number": "4155552671", "countryCode": country_code}


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

    Real profile: the configured real mailbox, plus-addressed (``you+qa-<token>@co``).
    """
    if real_data_enabled():
        return _plus(_real()["contact"]["email"], f"qa-{_token(8)}")
    return f"qa.auto+{_fake.user_name()}-{_token()}@{domain}"


def unique_domain(tld: str = "com") -> str:
    """Return a syntactically-valid domain unique ACROSS runs (for tenantDomain etc.).

    ``fake.unique.domain_name()`` repeats across runs (same reason as ``unique_email``);
    a persisted tenant domain then collides. The ``qa-auto-`` label keeps it identifiable
    and bulk-cleanable, and the uuid token guarantees global uniqueness.

    Real profile: ``<deal.domain>-<token>.<tld>`` (callers that need the bare label
    keep splitting on the first dot, as they already do).
    """
    if real_data_enabled():
        return f"{_real()['deal'].get('domain', 'demo')}-{_token(6)}.{tld}"
    return f"qa-auto-{_token(10)}.{tld}"


def unique_tenant_domain() -> str:
    """Return a bare subdomain LABEL for ``tenantDomain`` — no dots, no TLD.

    The BE validates this field as "lowercase letters, numbers and hyphens only (e.g.
    'saigon-logistics'), not beginning or ending with a hyphen", so a dotted domain like
    ``qa-auto-1234.com`` is REFUSED with 400 (verified live 2026-10-08). The UI tests
    already stripped the TLD by hand (``unique_domain().split(".")[0]``); this names the
    rule once so the API payloads stop disagreeing with it.
    """
    return unique_domain().split(".")[0]


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
        "phone": phone_detail(),
        "website": _fake.url(),
    }
    if real_data_enabled():
        r = _real()
        tok = _token(6)
        data.update(
            name=f"{r['partner']['name']} {tok}",
            email=_plus(r["contact"]["email"], f"partner-{tok}"),
            phone=_real_phone(),
            website=r["partner"].get("website") or data["website"],
        )
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
    if real_data_enabled():
        c = _real()["contact"]
        data.update(
            email=_plus(c["email"], f"user-{_token(6)}"),
            firstName=c.get("first_name") or data["firstName"],
            lastName=c.get("last_name") or data["lastName"],
        )
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
        "tenantDomain": unique_tenant_domain(),
        "prospectName": tag(f"{_fake.company()} Opportunity {_token(8)}"),
        "prospectEmail": unique_email(),
        "prospectPhone": phone_detail(),
        "prospectCountry": "US",
        "estimatedAcvCents": _fake.random_int(min=1_000_00, max=5_000_000_00),
        "currency": "USD",  # required by CreateDealDto (ISO 4217) — ACV/plan-budget currency
        "numberOfEmployee": _fake.random_int(min=10, max=5000),
        "billingCycle": "annual",
        "expectedCloseDate": "2026-12-31",
        "notes": tag(_fake.sentence()),
    }
    if real_data_enabled():
        r = _real()
        d, c = r["deal"], r["contact"]
        tok = _token(6)
        data.update(
            # A bare subdomain LABEL, as the BE DTO example ('saigon-logistics') and the
            # wizard's domain rule expect — unique per record.
            tenantDomain=f"{d.get('domain', 'demo')}-{tok}",
            prospectName=f"{d['company']} {tok}",
            prospectEmail=_plus(c["email"], f"deal-{tok}"),
            prospectPhone=_real_phone(),
            prospectCountry=c.get("country", "VN"),
            numberOfEmployee=int(d.get("headcount") or data["numberOfEmployee"]),
            notes=f"Real-data run ({tok})",
        )
    data.update(overrides)
    return data


def make_win_intake(
    plan_id: str, tenant_domain: str | None = None, **overrides: Any
) -> dict[str, Any]:
    """Build a ``WinDealDto`` body (POST /v1/sa/deals/{id}/win).

    In BOTH profiles ``tenantDomain`` is the DEAL's own domain when ``tenant_domain`` is
    passed, so registration and win never disagree (the BE takes ``dto.tenantDomain`` over
    the deal's, so a mismatch would provision a tenant under a domain nobody registered),
    and ``adminPhoneNumber`` is always sent — the win requires it (the UI's "reuse prospect
    phone" fallback does not fire). countryCode is ISO alpha-2, like every PhoneDetail.
    Real profile: the tenant admin is the configured real person (credentials mail lands
    in their inbox, plus-addressed per run); company/industry/region come from the YAML.
    """
    data: dict[str, Any] = {
        "companyWebsite": "https://qa-auto-win.example.com",
        "industry": "Technology",
        "adminFirstName": "QA",
        "adminLastName": "AutoWin",
        "adminEmail": "qa.auto+win@mailinator.com",
        "companyName": "QA-AUTO Won Co",
        # A bare LABEL, never a dotted domain: the BE refuses "qa-auto-won.example.com"
        # with 400 "not valid … lowercase letters, numbers and hyphens only" (2026-10-08).
        # Unique per call so a second run never collides with the tenant the first one won.
        "tenantDomain": tenant_domain or unique_tenant_domain(),
        # National-format number + ISO alpha-2 matching `country` below.
        "adminPhoneNumber": {"number": "4155552671", "countryCode": "US"},
        "planId": plan_id,
        "billingCycle": "annual",
        "numberOfEmployee": 42,
        "region": "asia-southeast1",
        "country": "US",
        "actualAcvCents": 7_500_000,
        "notes": "QA-AUTO win",
    }
    if real_data_enabled():
        r = _real()
        d, c = r["deal"], r["contact"]
        tok = _token(6)
        domain = tenant_domain or f"{d.get('domain', 'demo')}-{tok}"
        data.update(
            tenantDomain=domain,
            companyWebsite=f"https://{domain}.example.com",
            industry=d.get("industry") or data["industry"],
            adminFirstName=c.get("first_name") or data["adminFirstName"],
            adminLastName=c.get("last_name") or data["adminLastName"],
            adminEmail=_plus(c["email"], f"tenant-{tok}"),
            companyName=f"{d['company']} {tok}",
            numberOfEmployee=int(d.get("headcount") or data["numberOfEmployee"]),
            region=d.get("region") or data["region"],
            country=c.get("country", "VN"),
            adminPhoneNumber=_real_phone(),
            notes=f"Real-data win ({tok})",
        )
    data.update(overrides)
    return data
