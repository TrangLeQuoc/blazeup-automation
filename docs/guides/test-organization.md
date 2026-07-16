# Test Organization (Test Taxonomy)

How to classify, name, group, and write tests for the BlazeUp framework — so the
suite does **not become messy** as it grows. Read alongside:
[test-data.md](test-data.md) (factory + cleanup),
[add-domain.md](add-domain.md) (adding a new domain).

> **Golden rule (read before everything else):**
> **1 test case = 1 `test_…` function = 1 row in the test plan.** Every test is
> **independent, self-setup, self-cleanup**. No test depends on the run order of
> another test.

---

## 1. Three axes of organization

Every test is located by 3 axes, mapping directly onto the directory structure:

| Axis | Question | Example |
|------|---------|-------|
| **Domain** | Which app? | `blazeup` (one domain; SA + partner actors share it) |
| **Layer** | Which layer? | `api` (HTTP contract) · `ui` (browser) · `e2e` (business flow) |
| **Group** | Where does it belong? | API → by **feature/resource** · UI → by **page** |

```
tests/<domain>/
  api/<module>/   # group by RESOURCE/feature → api/partner/test_sa_deals.py, test_sa_partners.py
  ui/<module>/    # group by PAGE            → ui/dashboard/test_dashboard.py · ui/shell/test_page_loads.py
  e2e/            # group by JOURNEY (multi-step, stateful) → test_partner_onboarding.py (add when needed)
```

- **API grouped by feature/resource**, NOT by page (1 API serves many pages).
- **UI grouped by page**, one file per page.
- Within a layer, files sit in a **`<module>/` subfolder** (the module declared in
  `config/<domain>/config.yaml`) — e.g. `api/partner/`, `ui/dashboard/`, `ui/shell/`. This
  keeps modules separate as the suite grows; API clients mirror it under
  `api_clients/<domain>/<module>/`. (`sync_registry` scans recursively, so the subfolder
  never affects TC IDs.)
- **`e2e/`** is the ONLY place for multi-step scenarios that depend on each other (see §3).

---

## 2. Three types of test — which to use when

| Type | Purpose | Characteristics | Location |
|------|----------|----------|------|
| **Atomic contract** | Check 1 endpoint / 1 behavior | Independent, self setup+cleanup, can run in parallel | `api/`, `ui/` |
| **Negative / validation** | Wrong input → correctly rejected | Like atomic, but asserts errors (400/403/409…) | next to atomic, same feature |
| **E2E scenario** | End-to-end business flow | Multiple steps **sharing state**, sequential | `e2e/` |

**Decision rule:**

- Check "does this API return the correct contract?" → **atomic**.
- Check "is garbage input blocked?" → **negative** (a separate TC, do not cram into positive).
- Check "partner registers → SA approves → creates deal → computes commission" (each step
  uses the result of the previous step) → **E2E** in `e2e/`.

> ⚠️ **DO NOT** turn an atomic API test into a chain of interdependent steps. Implicit
> dependency = cannot run alone/in parallel, one failure drags along a mass of "false
> failures", hard to find the source of the error. That is exactly what makes a suite
> messy.

---

## 3. E2E scenario — when & how to write it

Only use when the steps **truly depend on state** (a record created in step 1 is used by
step 4). Still **1 function = 1 TC**, the steps are `async_step` (not split into multiple
interdependent functions).

```python
async def test_partner_onboarding_e2e(sa_partners_client, created_resources):
    async with async_step("[1/4] Register partner (pending)"):
        partner = await sa_partners_client.create_partner(make_partner())
        created_resources.add(lambda: sa_partners_client.delete_partner(partner.partner_id))
    async with async_step("[2/4] SA approves → active"):
        ...
    async with async_step("[3/4] Create deal for partner"):
        ...
    async with async_step("[4/4] Verify commission is computed"):
        ...
```

Whichever step fails goes red in Allure → you instantly know where the chain broke, while
the test is still an independent, self-cleaning unit.

---

## 4. Naming & TC ID

Function name → TC ID is generated automatically by `utils/sync_registry.py` (uppercase +
module lookup).

**Function naming convention:**
```
test_{module}_{layer}_{section}_{seq}
        │        │        │        └─ sequence (written 3-digit for readability, e.g. 002,
        │        │        │           011, 033; packed as 2 digits in the ID → 01–99 / section)
        │        │        └─ sub-section/feature within the module
        │        └─ api | ui
        └─ module (must be declared in config/<domain>/config.yaml)
```
Example: `test_partner_api_partner_account_management_002`
→ `PARTNER_API_PARTNER_ACCOUNT_MANAGEMENT_002` → ID `2060102`.

**ID formula (8 digits):** `{type}{project}{module:02d}{section:02d}{seq:02d}`
- `type`: **1 = UI**, **0 = API** — an API id starts with `0`, so it displays as 7 digits (e.g. `2060102`); a UI id keeps all 8 (e.g. `12020101`)
- `project`: the domain's digit (`blazeup` = 2) — keeps IDs distinct across projects even if module names collide
- `module` / `section`: 2 digits each, from `config.yaml` (`modules.<NAME>.number` + the `ui:`/`api:` section map)
- `seq`: **2 digits** (`01`–`99`) — max 99 TCs per section

> Sections are numbered **incrementally as they are written**, they do NOT need to be
> contiguous in meaning. E.g. validation being `_011` right after `_010` is normal —
> **filter by marker/Test Type, do not rely on sequence numbers** for grouping.

Added a new test but the ID isn't recognized? → the module/section must exist in
`config/<domain>/config.yaml`, then run `python utils/sync_registry.py`.

---

## 5. Markers — classify to filter at run time

Declared in `pytest.ini`. Use markers to **filter at run time**, do NOT split into
separate directories by type.

| Marker | Meaning | When to apply |
|--------|-------|-------------|
| `@pytest.mark.smoke` | Vital set, runs fast on every commit | A few TCs proving the system "breathes" |
| `@pytest.mark.regression` | Full suite, run before release | Most TCs |
| `@pytest.mark.api` | HTTP-layer test | Every test in `api/` |
| `@pytest.mark.ui` | Browser test | Every test in `ui/` |
| `@pytest.mark.slow` | Slow / multi-step E2E | E2E, scheduled jobs |
| `@pytest.mark.be_gap` | Known BE gap, **intentionally red** until BE fixes it (per §6 rule 4) | A TC whose main check step fails because the BE lacks logic |

> **Separate the pass/fail signal:** a TC marked `be_gap` still FAILs to report the gap
> (rule 4), but the **merge gate runs `-m "not be_gap"`** so 100% green = no regression. A
> separate job runs `-m be_gap` to track BE gaps (allowed to be red). This way "known
> reds" do not mask "new reds".

```bash
python -m runner.<domain>.run_test --mode smoke        # smoke only
python -m runner.<domain>.run_test --type api          # API only
pytest -m "regression and not slow"                    # filter directly
```

Application convention: **each test ≥ 1 layer marker (`api`/`ui`) + 1 scope marker
(`smoke`/`regression`)**. `--strict-markers` requires markers to be declared first.

---

## 6. Positive vs Negative

- **Positive**: correct path → correct result (e.g. create a valid partner → 201, pending).
- **Negative**: wrong input/condition → correctly rejected (e.g. missing field → 400 +
  message naming the field + NO record created).

Negative is a **separate TC** (its own row in the test plan), not mixed into positive.
Place it next to the corresponding feature. The **Test Type** column states clearly
`Functional` / `Negative` / `Security`.

### Mandatory rules for writing test cases

1. **Positive → paired with Negative.** After finishing a positive TC, immediately do the
   corresponding negative (if the business logic has one) — do not leave one side empty.
2. **Cover FULL params.** Each TC self-sweeps everything:
   - *Positive:* send **every** field (required + optional) and **assert echoed** for each
     one (catch silent-mutation) + lifecycle/side-effects.
   - *Negative:* **every** required field as missing, + invalid enum, + wrong format
     (email/date), + boundary (negative/0/extremely large), + non-existent FK.
   - Take enum values from the **OpenAPI spec**; do not guess.
3. **A param that is a foreign key (FK) → prove "does not exist" INSIDE the test.** If a
   param points to another service's data (`planId`→sa-plans, `partnerId`→partners,
   `userId`→partner-users…), when creating ghost data for negative you must **GET-by-id at
   the source service and assert its absence (4xx) RIGHT INSIDE the test**, then use it.
   Absolutely do not hard-code an id and assume. If the source service reports "exists" →
   the fixture is wrong → fail clearly ("fixture invalid") instead of producing a
   misleading result.
   - *Exception:* if the very endpoint under test already returns "not found" for the ghost
     id (self-proving in the assert) then a separate GET is not needed (e.g. ghost
     `partnerId` when registering a deal). You only need to GET the source when the endpoint
     does **not** self-report (e.g. a `planId` that gets accepted with 201 → you must prove
     absence from sa-plans).
4. **BE missing validation → fail for real + report to BE.** Do not write a fake-green
   test; let that step FAIL with the message "confirm with BE", and record the gap in the
   TC's Note.
5. **Auth/Permission always has 3 basic TCs** (for a protected endpoint):
   - No token → **401**
   - Wrong role/permission → **403**
   - A token of a different entity trying to access a resource that is not its own → **403 or 404**
     (target/guideline; on BlazeUp SA this currently returns **400** — still refused, no data
     leak — see `PARTNER_API_AUTH_ACCESS_CONTROL_003`. Assert the real code; refusal is what matters.)
   - *(Auth is usually grouped under the Auth & Access Control feature, not crammed into each functional TC — but it must exist.)*
6. **Each TC is self-contained:**
   - Set up fixture/data **within the TC itself** — do not use data created by another TC.
   - **Cleanup** after running (`created_resources`), clean whether it passes or fails.
   - State the **precondition state** clearly (e.g. "deal must be FLAGGED", "partner must be pending").
7. **Assert schema, not just assert value:**
   - Check the **type** of the returned field (list/dict/int/str…), not just the value.
   - Check that **sensitive fields are not leaked** in the response (password, token, secret…).
   - Check that **required fields are always present** (id, status, code…).
8. **Duplicate/Idempotency for every POST that creates a resource:**
   - Call twice with the same payload → **state the expected behavior clearly**: 409 (reject
     the duplicate) or idempotent (no-op/return the existing one)? Assert exactly that, do
     not leave it ambiguous.
   - **It is a SEPARATE TC** (its own row in the test plan, Test Type = `Negative`), placed
     next to the create feature — DO NOT cram it as the last step of the positive TC
     (combining 2 purposes → positive goes red for a duplicate reason, and reading the log
     you mistake it for "create failed"). The ONLY exception: if resending is a real step in
     an `e2e/` scenario (e.g. a user clicks submit twice due to the network) then it is an
     `async_step`, not atomic.
   - **Only apply the formula above to POST that _creates a resource_.** For a create POST,
     calling twice producing 2 records = BUG → the correct answer is fixed (reject **or**
     idempotent), assert it straight. For a **mutating action with a parameter** (e.g.
     `extend-protection` +N days, change tier, add points…), repeating CAN be correct in 2
     ways — **additive** (accumulates) or **capped** (blocks the 2nd time) — **both can be a
     feature**. Do not blindly apply 409/idempotent: **probe / ask BE** what the intent is
     before asserting (this is a "define behavior on repeat" edge, not duplicate-create).
9. **Update the test case documentation after finishing.** Every time you finish writing (or
   editing) a TC, you must update **both files** with the corresponding TC content
   (description + steps with → Expected + overall + note; if it is a gap then state "confirm
   BE" clearly):
   - `docs/blazeup/PARTNER_TEST_CASES.md` (EN)
   - `docs/blazeup/PARTNER_TEST_CASES_vi.md` (VI)
   - NOT_STARTED just has the name; BLOCKED records the reason; PASSED/FAILED records the
     full detail. Keep the 2 files in sync with the code + the Excel test plan.

---

## 7. Anatomy of a good test

```python
@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_partner_account_management_002(sa_partners_client, created_resources):
    """<TC ID>: <one-line description>.  <explanation of the contract being checked>."""
    # SETUP: build unique data (factory) — log exactly the field to be asserted
    payload = make_partner(type="channel")
    logger.info("SETUP: payload → name='{}', email='{}'", payload["name"], payload["email"])

    async with async_step("[1/N] Call API ..."):
        resp = await sa_partners_client.create_partner(payload)
        created_resources.add(lambda: sa_partners_client.delete_partner(resp.partner_id))  # clean up BEFORE assert

    async with async_step("[2/N] Verify ..."):
        assert ...
        logger.info("CHECK ... → OK (...)")

    logger.info("RESULT: ...")
```

Mandatory components:

| Part | Role |
|------|---------|
| **Docstring** | First line = `<TC ID>: <description>`; then explain the contract |
| **Marker** | layer + scope (§5) |
| **`SETUP:`** | build data (factory, [test-data.md](test-data.md)); log the field to be asserted |
| **`async_step("[n/N] …")`** | each step → 1 Pass/Fail node in Allure ([log_helper](../../utils/log_helper.py)) |
| **`CHECK … → OK`** | each assertion logs 1 line → reads like a checklist |
| **`created_resources.add(...)`** | register cleanup **right after creating, before assert** |
| **`RESULT:`** | final result |

Request/response is **logged automatically + attached to the Allure step** by `BaseClient`
— no need to log the payload manually.

---

## 8. Anti-mess checklist

Before committing a test, ask yourself:

- [ ] Is this one function = exactly 1 TC in the test plan? (not combining 2 purposes)
- [ ] Can it run **alone**? (not dependent on another test)
- [ ] Does it **clean up** the data it created? (`created_resources`)
- [ ] Is the data **unique**? (factory `fake.unique`, prefix `QA-AUTO`)
- [ ] Does it have a layer + scope **marker**?
- [ ] Does the function name match the convention → does `sync_registry` produce the right ID?
- [ ] Are positive/negative split into the correct test plan rows?
- [ ] Is each step wrapped in `async_step`, does each assert have a `CHECK`?

---

## 9. When to restructure

- **< 20 TCs**: keep it flat under `api/` `ui/`. Do not optimize early.
- **20–50 TCs**: one file per feature/page; group into `<module>/` subfolders. Standardize markers.
- **> 50 TCs** (current state): grouped by module under `api/<module>/` · `ui/<module>/`
  (see §1); split out `e2e/` when real multi-step flows appear; maintain a clear smoke-set.
