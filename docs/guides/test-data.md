# Test data management (Faker + cleanup)

Goal: each test has **unique** data (parallel runs don't collide) and
**cleans up automatically** when done (staging stays clean, results are stable).

## 2 tools

| Tool | File | Used for |
|---|---|---|
| **Factory** | `utils/data_factory.py` | Generate unique payloads, tagged `QA-AUTO` |
| **Cleanup fixture** | `created_resources` (in `pytest_support/fixtures.py`) | Register a resource for deletion → teardown calls it automatically (even when the test fails) |

## 1. Factory — generate data

```python
from utils.data_factory import make_user, make_tenant, make_deal

make_user()                       # all fields random + unique email
make_user(department="Finance")   # override 1 field to assert on
make_tenant()                     # name has prefix "QA-AUTO ..."
```
- `fake.unique.*` guarantees **no duplicates** within a single run.
- Human-readable fields carry the **`QA-AUTO`** prefix → easy to identify + clean up in bulk.
- Returns a plain `dict` → pass it straight into `client.post(..., json=...)`.

> The fields in the factory are a **reasonable starting point**, not the official
> backend schema. Once the API finalizes its contract, adjust the fields to match.

## 2. Cleanup — auto-delete after the test

The `created_resources` fixture: register one delete callback for **everything you create**.
Teardown runs the callbacks in **reverse** order (LIFO), swallowing errors (only logging them) so
one failed cleanup doesn't block another.

```python
import pytest
from utils.data_factory import make_tenant


@pytest.mark.api
@pytest.mark.regression
async def test_create_tenant_001(auth_client, created_resources):
    """TENANT_API_CREATE_001: creating a new tenant via API returns 201 + has an id."""
    # ── Arrange + Act: create via API (faster, more stable than clicking the UI) ──
    payload = make_tenant()
    resp = await auth_client.post("/tenants", json=payload, expected_status=201)
    tenant_id = resp.json()["data"]["id"]

    # ── Register cleanup RIGHT after creating (before asserts) to be sure it gets deleted ──
    created_resources.add(lambda: auth_client.delete(f"/tenants/{tenant_id}"))

    # ── Assert ──
    assert tenant_id, "Tenant must have an id after creation"
    # → teardown deletes this tenant automatically, whether the test passes or fails.
```

### Golden rules
1. **Register cleanup RIGHT after creating** (before the asserts) — if an assert fails
   partway through, the resource still gets cleaned up.
2. **Prefer creating/deleting via API** in setup/teardown (fast, less flaky) — even when
   the main test is a UI test.
3. **Don't assume data already exists** — the test creates what it needs (test isolation).

## 3. Test isolation

- Each test owns its own data → running in **any order / in parallel / individually** yields the same result.
- `authenticated_page` already gives each test its own browser context (cookies are not shared).
- `created_resources` ensures no leftover junk between tests.

## 4. When to use

- Tests that **only read/check** (e.g. loading a page) → **no need** for factory/cleanup.
- **CRUD** tests (create/update/delete tenant, partner, deal, user...) → **must** use both.

## 5. Business rules — don't hard-code what the product derives

Some values a test checks are not data the test chose — the product **derives** them from
the account under test. Hard-code one and the test breaks the day the account or the
derivation changes, while the product is fine (TC 12060208/211 hard-coded "Referral" and
failed when the Channel test partner correctly got "Reseller", 2026-10-13).

Those rules live in **`utils/partner_rules.py`** — the single source, mirroring
requirement 2.2 ("4 Partner Types"):

| Partner type (API `type`) | SA label | Requirement 2.2 | Billing model | Deal type in the wizard |
|---|---|---|---|---|
| `channel` | Channel | Reseller/VAR | reseller | **Reseller** (observed 2026-10-14) |
| `referral` | Referral | Referral | direct | **Referral** |
| `system_integrator` | System Integrator | SI | direct | *not defined* |
| `msp` | MSP | MSP | partner_managed | *not defined* |

There is no partner type called "Reseller" — the requirement's Reseller/VAR is the SA's
**Channel**. Don't confuse partner types with **deal** types (`referral` / `reseller` /
`co_sell`).

How to use it:

```python
from utils.partner_rules import RuleNotSpecified, expected_deal_type

async def test_x(make_partner_page, partner_profile):
    try:
        rule = expected_deal_type(partner_profile["type"])   # the UI account's own type
    except RuleNotSpecified as exc:
        pytest.skip(f"BLOCKED: {exc}")                        # never guess an undefined rule
    assert await wizard.dialog().get_by_text(rule.deal_type_label).is_visible()
```

- `partner_profile` (session fixture) gives the portal UI account's `code` / `type` /
  `tier`. It is read **before** any UI login — the partner refresh token is single-use, so
  an API login after the browser logged in would kill the browser session.
- A rule the requirement does **not** state is `None` in the table. `expected_deal_type`
  then raises `RuleNotSpecified` and the test reports **BLOCKED** (ask the PO) — it must
  not pass or fail on an invented expectation.
- New rule? Add it to the table **with its source** (`evidence`), and extend
  `selftests/test_partner_rules.py`.

## Checklist for writing a CRUD test
- [ ] Use `make_*()` to generate the payload (don't hard-code).
- [ ] Create the resource via the API client (`auth_client.post(...)`).
- [ ] `created_resources.add(lambda: client.delete(...))` right after creating.
- [ ] Assert the behavior.
- [ ] (No need to write teardown manually — the fixture handles it.)
