"""Test data factories — generate unique, identifiable payloads with Faker.

Why factories instead of hard-coded data:
  * Uniqueness  — every record gets fresh values (``fake.unique.*``), so tests
    never collide on "already exists" and are safe to run in parallel (-n auto).
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

from typing import Any

from faker import Faker

# Module-level generator. `.unique` guarantees no repeats within a test process.
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


def unique_email(domain: str = "mailinator.com") -> str:
    """Return a unique, tagged email address safe for parallel runs."""
    # local-part includes a unique token; '+' tagging keeps it one real inbox.
    return f"qa.auto+{_fake.unique.user_name()}@{domain}"


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
        "domain": _fake.unique.domain_word(),
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
    each other (a deal in test A flags against a deal in test B). ``fake.unique``
    guarantees no repeat within the process.

    Reuse the SAME returned dict for both partners in a conflict test to create
    the intended same-prospect collision::

        prospect = make_prospect()
        await client.register_deal(make_deal(p1, plan, **prospect))
        await client.register_deal(make_deal(p2, plan, **prospect))  # flagged
    """
    data: dict[str, Any] = {
        "prospectName": tag(f"{_fake.unique.company()} Prospect"),
        "prospectEmail": unique_email(),
    }
    data.update(overrides)
    return data


def make_deal(partner_id: str, plan_id: str, **overrides: Any) -> dict[str, Any]:
    """Build a deal-registration payload matching ``CreateDealDto`` (sa-partners-api).

    Required by the API: ``partnerId``, ``dealType`` (referral / reseller / co_sell),
    ``prospectName``, ``prospectCountry``, ``estimatedAcvCents``, ``expectedCloseDate``,
    plus ``planId`` (a published billing plan; or pass an inline ``billingPlan``).
    """
    data: dict[str, Any] = {
        "partnerId": partner_id,
        "planId": plan_id,
        "dealType": "referral",
        "prospectName": tag(f"{_fake.company()} Opportunity"),
        "prospectEmail": unique_email(),
        "prospectPhone": valid_phone(),
        "prospectCountry": "US",
        "estimatedAcvCents": _fake.random_int(min=1_000_00, max=5_000_000_00),
        "expectedCloseDate": "2026-12-31",
        "notes": tag(_fake.sentence()),
    }
    data.update(overrides)
    return data
