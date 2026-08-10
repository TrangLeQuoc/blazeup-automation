"""Partner Portal — Register-a-Deal wizard, step 1 (UI, MY_PIPELINE).

    PARTNER_UI_MY_PIPELINE_001 — enter valid company details → wizard advances to
                                 the next step and preserves the company data.
    PARTNER_UI_MY_PIPELINE_002 — leave company name blank → the wizard blocks
                                 advancing (required-field guard).

The wizard validates by DISABLING "Next" until the step's required fields are
filled (there is no inline error text on this build — see locator notes). These
tests exercise the modal only (open → fill/validate → advance/back); they do NOT
submit, so they create no deal and need no cleanup (and are unaffected by the
deals-list BE defect blocking _024/_025).
"""

import asyncio
import time

import httpx
import pytest
from loguru import logger

from api_clients.blazeup.partner.auth_client import PartnerAuthClient
from config.settings import Settings
from pages.blazeup.partner.partner_shell_page import PartnerShellPage
from pages.blazeup.partner.register_deal_wizard import RegisterDealWizard
from utils.data_factory import unique_domain, unique_email
from utils.log_helper import async_step
from utils.login_helpers import login_api

_fake_company = "QA-AUTO Wizard Co"


async def _wait_captured(page, captured: dict, timeout_ms: int = 30_000) -> None:
    """Wait until the response listener filled *captured*, instead of sleeping.

    The register POST is captured by a ``page.on("response")`` handler, so the test has
    a precise signal for "the answer arrived" — a flat sleep was both a guess and a
    guaranteed cost. Tolerant on timeout: the caller asserts on *captured* and its
    message is the useful evidence.
    """
    deadline = time.perf_counter() + timeout_ms / 1000
    while time.perf_counter() < deadline:
        if captured:
            return
        await page.wait_for_timeout(200)


# Subdomain labels to probe for a RESERVED one (check-domain available=false).
_DOMAIN_CANDIDATES = ("test", "demo", "acme", "staging", "sales", "production")


async def _classify_domains(settings: Settings) -> tuple[str | None, str | None]:
    """Return (taken_label, available_label) via the partner check-domain API.

    Proves — independently of the UI — which subdomain label is already reserved
    (available=false) vs free (available=true), so the UI warning assertion is not
    circular.
    """
    api = str(settings.api_base_url).rstrip("/")
    pbase = str(settings.partner_base_url).rstrip("/")
    token = await login_api(
        api,
        pbase,
        settings.partner_email,
        settings.partner_password,
        auth_cls=PartnerAuthClient,
        totp_secret=settings.partner_totp_secret,
    )
    headers = {"Authorization": f"Bearer {token}", "Origin": pbase}
    taken = available = None
    async with httpx.AsyncClient(timeout=30) as h:
        for label in _DOMAIN_CANDIDATES:
            resp = await h.get(
                f"{api}/sa-partners-api/v1/partner/portal/check-domain?domain={label}",
                headers=headers,
            )
            data = resp.json().get("data") or {}
            if data.get("available") is False and taken is None:
                taken = label
            if data.get("available") is True and available is None:
                available = label
    return taken, available


async def _open_deals(shell: PartnerShellPage) -> None:
    await shell.open("deals")
    await shell.wait_ready("deals")


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_001(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_001: valid company details advance the wizard + preserve data.

    Plan-vs-live: the plan says "advances to the contact step", but on the live
    wizard the primary contact is part of step 1 ("Register company"); a valid
    step 1 advances to step 2 ("Deal info"). This drives the real wizard.
    """
    shell = make_partner_page(PartnerShellPage)
    wiz = make_partner_page(RegisterDealWizard)
    company = f"{_fake_company} {unique_domain().split('.')[0]}"
    domain = unique_domain().split(".")[0]  # the Domain field is a bare subdomain label
    contact_name = "QA-AUTO Contact"
    contact_email = unique_email()

    async with async_step("Setup: open Deals and launch the Register-a-Deal wizard"):
        await _open_deals(shell)
        await wiz.open()
        assert await wiz.step_text() == "Step 1 of 3", "wizard should open on step 1 of 3"

    async with async_step(
        "[1/3] Enter company details + contact; verify each field holds the value"
    ):
        await wiz.fill_company(company, domain)
        await wiz.select_first_country()
        await wiz.fill_contact(contact_name, contact_email)
        await wiz.wait_step("Step 1 of 3")  # hold so the filled step-1 form is visible on video
        # Echo: each field actually accepted the entered value (no silent mutation/clear).
        assert await wiz.company_value() == company, (
            f"company name field must hold {company!r}, got {await wiz.company_value()!r}"
        )
        assert await wiz.domain_value() == domain, (
            f"domain field must hold {domain!r}, got {await wiz.domain_value()!r}"
        )
        assert await wiz.contact_name_value() == contact_name, "contact name field lost its value"
        assert await wiz.contact_email_value() == contact_email, (
            "contact email field lost its value"
        )
        assert await wiz.country_selected(), "a country must be selected ('Select country' gone)"
        logger.info(
            "CHECK echo → OK (name/domain/contact/email hold entered values, country picked)"
        )
        # Required-completeness: with all required fields filled, Next is enabled.
        assert await wiz.next_enabled(), (
            "with all required step-1 fields filled, 'Next' must be enabled — it is disabled"
        )
        logger.info("CHECK required → OK (all required filled → Next enabled)")

    async with async_step("[2/3] Click Next → wizard advances to the next step"):
        await wiz.click_next()
        await wiz.wait_step("Step 2 of 3")  # wait for the transition + hold for the video
        assert await wiz.step_text() == "Step 2 of 3", (
            f"wizard must advance to step 2, still on '{await wiz.step_text()}'"
        )
        # Light check that it landed on the Deal-info CONTENT (a step-2-only field),
        # not just that the counter changed. Deep Deal-info testing is _008–_012.
        assert await wiz.deal_info_visible(), (
            "step 2 should render the Deal info content (e.g. 'Expected close date' field)"
        )
        logger.info("CHECK advance → OK (Step 2 of 3, Deal info content rendered)")

    async with async_step("[3/3] Company data is preserved (go Back → company name intact)"):
        await wiz.click_back()
        await wiz.wait_step("Step 1 of 3")  # wait for the transition + hold for the video
        assert await wiz.step_text() == "Step 1 of 3", "Back should return to step 1"
        assert await wiz.company_value() == company, (
            f"company name must be preserved, got {await wiz.company_value()!r}"
        )
        logger.info("CHECK preserved → OK (company name intact after Back)")

    logger.info("RESULT: valid company details advance the wizard and preserve the data")


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_002(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_002: blank company name blocks the wizard from advancing.

    Negative counterpart of _001. Plan wording is "required field error is shown";
    on this build the wizard enforces required fields by DISABLING "Next" (no inline
    error text), so the assertion is: with company name blank, the wizard cannot
    advance; filling it enables advancing — proving company name is required.
    """
    shell = make_partner_page(PartnerShellPage)
    wiz = make_partner_page(RegisterDealWizard)
    domain = unique_domain().split(".")[0]  # the Domain field is a bare subdomain label
    contact_name = "QA-AUTO Contact"
    contact_email = unique_email()

    async with async_step("Setup: open Deals and launch the Register-a-Deal wizard"):
        await _open_deals(shell)
        await wiz.open()

    async with async_step("[1/2] Only company name blank (others filled) → cannot advance"):
        await wiz.fill_company(None, domain)  # company name left blank
        await wiz.select_first_country()
        await wiz.fill_contact(contact_name, contact_email)
        # Isolate the cause: the OTHER required fields are all filled, and company is truly blank,
        # so Next being disabled is attributable ONLY to the missing company name.
        assert await wiz.company_value() == "", "precondition: the company name must be blank"
        assert await wiz.domain_value() == domain, "domain (other required field) must be filled"
        assert await wiz.country_selected(), "country (other required field) must be selected"
        assert await wiz.contact_name_value() == contact_name, "contact name must be filled"
        assert await wiz.contact_email_value() == contact_email, "contact email must be filled"
        assert not await wiz.next_enabled(), (
            "with only company name blank (others filled), 'Next' must stay disabled"
        )
        assert await wiz.step_text() == "Step 1 of 3", "wizard must not advance with company blank"
        logger.info(
            "CHECK isolated → OK (only company blank; others filled; Next disabled → step 1)"
        )

    async with async_step("[2/2] Fill the company name → advancing becomes possible"):
        await wiz.fill_company("QA-AUTO Now Valid", unique_domain().split(".")[0])
        assert await wiz.next_enabled(), (
            "filling the company name must enable 'Next' — proving it was the blocking required field"
        )
        logger.info("CHECK filled → OK (Next enabled once company name provided)")

    logger.info(
        "RESULT: blank company name blocks advancing; providing it unblocks — required enforced"
    )


# Clearly-malformed domains that a "domain format" validation must reject.
_INVALID_DOMAINS = ("@@@", "ab cd", "notadomain", "http://x.com")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.be_gap
async def test_partner_ui_my_pipeline_003(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_003: an invalid domain must be rejected with a format error.

    Negative (fail-by-design). With valid company/contact and a malformed domain, the
    wizard SHOULD reject it (block Next or flag the field). On this build it does NOT:
    every malformed domain (even '@@@' / 'ab cd') is accepted — Next stays enabled and
    the Domain field is not flagged. There is no domain-format validation, so this
    asserts the correct behaviour and fails until FE adds it. All cases run (collected).
    """
    shell = make_partner_page(PartnerShellPage)
    wiz = make_partner_page(RegisterDealWizard)

    async with async_step("Setup: open the wizard with valid company/country/contact"):
        await _open_deals(shell)
        await wiz.open()
        await wiz.fill_company("QA-AUTO Domain Neg", unique_domain().split(".")[0])
        await wiz.select_first_country()
        await wiz.fill_contact("QA-AUTO Contact", unique_email())

    async with async_step("[1/1] Each malformed domain must be rejected (block Next / flag field)"):
        accepted: list[str] = []
        for bad in _INVALID_DOMAINS:
            await wiz.fill_domain(bad)
            held = await wiz.domain_value()  # what the field actually kept
            rejected = (not await wiz.next_enabled()) or await wiz.domain_aria_invalid()
            if rejected:
                logger.info("CHECK domain {!r} → OK (rejected)", bad)
            else:
                # Proof the app took the garbage value AND still lets the deal proceed.
                accepted.append(f"{bad!r} (field kept {held!r}, Next enabled, not flagged)")
        assert not accepted, (
            f"wizard accepts invalid domain(s) {accepted} — no domain-format validation on the "
            f"register wizard. Confirm with FE."
        )

    logger.info("RESULT: domain-format validation enforced on the register wizard")


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_004(make_partner_page, settings):
    """PARTNER_UI_MY_PIPELINE_004: an already-reserved domain shows an inline active-account warning.

    Entering a subdomain already reserved by another active deal must surface an
    inline warning (the deal would enter the conflict queue on submit). A free
    domain shows no warning (control). The reserved/free state is proven via the
    check-domain API first, so the UI assertion is not circular. UI-only (no submit).
    """
    taken, available = await _classify_domains(settings)
    if not taken:
        pytest.skip(
            f"BLOCKED: no reserved (available=false) domain among {_DOMAIN_CANDIDATES} to drive "
            f"the warning — cannot exercise the inline active-account warning."
        )
    available = available or unique_domain().split(".")[0]  # a definitely-free label (no dots)
    logger.info("Proven via check-domain API: taken={!r}, available={!r}", taken, available)

    shell = make_partner_page(PartnerShellPage)
    wiz = make_partner_page(RegisterDealWizard)

    async with async_step("Setup: open the wizard with valid company/country/contact"):
        await _open_deals(shell)
        await wiz.open()
        await wiz.fill_company("QA-AUTO Domain Warn", available)  # placeholder; overwritten below
        await wiz.select_first_country()
        await wiz.fill_contact("QA-AUTO Contact", unique_email())

    async with async_step("[1/2] Enter the RESERVED domain → inline active-account warning shows"):
        await wiz.fill_domain(taken)
        warning = await wiz.wait_domain_warning()
        assert warning, (
            f"a reserved domain ({taken!r}, proven available=false) must show an inline warning"
        )
        logger.info("CHECK reserved → OK (warning shown: {!r})", warning)

    async with async_step("[2/2] Enter an AVAILABLE domain → no warning (control)"):
        await wiz.fill_domain(available)
        await wiz.wait_domain_warning_cleared()
        assert await wiz.domain_warning_text() == "", (
            f"an available domain ({available!r}) must not show the reserved/active-deal warning"
        )
        logger.info("CHECK available → OK (no warning for a free domain)")

    logger.info("RESULT: reserved domain warns (conflict queue); available domain does not")


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_005(make_partner_page, partner_authenticated_page, settings):
    """PARTNER_UI_MY_PIPELINE_005: submit the full wizard on a RESERVED domain (conflict path).

    Fills the whole register wizard (company + contact + reserved domain, then deal
    info: plan / seats / region / expected close date) and SUBMITS. Asserts the
    reserved-domain warning appeared and the submission succeeded (a deal was created).

    PENDING (verify step — intentionally NOT asserted yet): confirming the deal
    actually LANDS in the conflict queue is deferred. The partner deals-list endpoint
    is currently 400 (see _024), so the created deal is not listable, and there is no
    delete API to clean it up. To be improved once BE provides a way to fetch/remove
    the created deal (user to supply the approach). The created deal id is logged so it
    can be located/cleaned manually.
    """
    taken, _ = await _classify_domains(settings)
    if not taken:
        pytest.skip("BLOCKED: no reserved domain to drive the conflict-queue submission")
    page = partner_authenticated_page
    shell = make_partner_page(PartnerShellPage)
    wiz = make_partner_page(RegisterDealWizard)

    submitted: dict = {}

    async def _on_resp(r):
        if r.request.method == "POST" and "/deals" in r.url:
            body = None
            try:
                body = await r.json()
            except Exception:  # noqa: BLE001 — best-effort capture
                body = None
            submitted.update(status=r.status, url=r.url, body=body)

    page.on("response", lambda r: asyncio.create_task(_on_resp(r)))

    async with async_step("Setup: open wizard; fill step 1 with a RESERVED domain"):
        await _open_deals(shell)
        await wiz.open()
        await wiz.fill_company(f"QA-AUTO Conflict {unique_domain().split('.')[0]}", taken)
        await wiz.select_first_country()
        await wiz.fill_contact("QA-AUTO Contact", unique_email())
        warning = await wiz.wait_domain_warning()
        assert warning, f"reserved domain {taken!r} must show the conflict warning before submit"
        logger.info("CHECK reserved warning → OK ({!r})", warning)

    async with async_step("[1/3] Advance to Deal info"):
        await wiz.click_next()
        await wiz.wait_step("Step 2 of 3")

    async with async_step("[2/3] Fill Deal info (plan, seats, region, expected close date)"):
        await wiz.pick_first_plan()
        await wiz.fill_seats(10)
        await wiz.pick_first_region()
        await wiz.pick_expected_close_date()
        assert await wiz.next_enabled(), "Deal info complete → 'Next' must be enabled"
        await wiz.click_next()
        await wiz.wait_step("Step 3 of 3")
        logger.info("CHECK deal-info → OK (advanced to Summary)")

    async with async_step("[3/3] Submit the deal"):
        label = await wiz.submit()
        await _wait_captured(page, submitted)
        if submitted:
            assert submitted["status"] in (200, 201, 202), f"deal submit failed: {submitted}"
            data = submitted.get("body") or {}
            deal_id = data.get("data", {}).get("_id") if isinstance(data, dict) else None
            logger.info(
                "CHECK submit → OK ('{}' → POST {} {}, dealId={})",
                label,
                submitted["url"],
                submitted["status"],
                deal_id,
            )
        else:
            txt = " ".join((await page.locator("body").inner_text()).split()).lower()
            assert any(
                k in txt for k in ("success", "registered", "submitted", "conflict", "pending")
            ), "no submission-success indicator found after submit"
            logger.info("CHECK submit → OK (UI success indicator present)")

    logger.warning(
        "PENDING (verify): conflict-queue landing is NOT asserted yet — partner deals-list is 400 "
        "(_024) and there is no delete API. Improve once BE provides fetch/remove for the deal."
    )
    logger.info(
        "RESULT: full wizard submitted on a reserved domain (conflict-queue verify pending)"
    )


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_006(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_006: blank contact email blocks the wizard (required-field guard).

    Negative counterpart (contact email). With every OTHER required field filled and
    only the contact email blank, the wizard cannot advance (Next stays disabled);
    filling the email enables advancing — proving the email is required. (This build
    enforces required fields by disabling Next; no inline error text.)
    """
    shell = make_partner_page(PartnerShellPage)
    wiz = make_partner_page(RegisterDealWizard)
    domain = unique_domain().split(".")[
        0
    ]  # the Domain field is a bare subdomain label.split(".")[0]
    contact_name = "QA-AUTO Contact"

    async with async_step("Setup: open the wizard"):
        await _open_deals(shell)
        await wiz.open()

    async with async_step("[1/2] Only contact email blank (others filled) → cannot advance"):
        await wiz.fill_company("QA-AUTO Email Req", domain)
        await wiz.select_first_country()
        await wiz.fill_contact(contact_name, "")  # email left blank
        assert await wiz.company_value() and await wiz.domain_value() == domain, (
            "company + domain (other required fields) must be filled"
        )
        assert await wiz.country_selected(), "country (other required field) must be selected"
        assert await wiz.contact_name_value() == contact_name, "contact name must be filled"
        assert await wiz.contact_email_value() == "", "precondition: contact email must be blank"
        assert not await wiz.next_enabled(), (
            "with only contact email blank (others filled), 'Next' must stay disabled"
        )
        logger.info("CHECK isolated → OK (only email blank; others filled; Next disabled)")

    async with async_step("[2/2] Fill a valid email → advancing becomes possible"):
        await wiz.fill_email(unique_email())
        assert await wiz.next_enabled(), (
            "filling a valid contact email must enable 'Next' — proving it was the blocking field"
        )
        logger.info("CHECK filled → OK (Next enabled once a valid email is provided)")

    logger.info("RESULT: blank contact email blocks advancing; a valid email unblocks")


# Malformed emails that an email-format validation must reject.
_INVALID_EMAILS = ("notanemail", "abc@", "abc@x", "a b@x.com")


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_007(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_007: a malformed contact email must be rejected with a format error.

    Negative (fail-by-design). With valid company/domain/country/contact-name and a
    malformed email, the wizard SHOULD reject it (block Next or flag the field). On
    this build it does NOT: every malformed email (even 'notanemail' / 'a b@x.com')
    is accepted — Next stays enabled and the field is not flagged. No email-format
    validation, so this asserts the correct behaviour and fails until FE adds it.
    """
    shell = make_partner_page(PartnerShellPage)
    wiz = make_partner_page(RegisterDealWizard)

    async with async_step("Setup: open the wizard with valid company/country/contact-name"):
        await _open_deals(shell)
        await wiz.open()
        await wiz.fill_company("QA-AUTO Email Neg", unique_domain().split(".")[0])
        await wiz.select_first_country()
        await wiz.fill_contact("QA-AUTO Contact", "placeholder@example.com")

    async with async_step("[1/1] Each malformed email must be rejected (block Next / flag field)"):
        accepted: list[str] = []
        for bad in _INVALID_EMAILS:
            await wiz.fill_email(bad)
            held = await wiz.contact_email_value()
            rejected = (not await wiz.next_enabled()) or await wiz.email_aria_invalid()
            if rejected:
                logger.info("CHECK email {!r} → OK (rejected)", bad)
            else:
                accepted.append(f"{bad!r} (field kept {held!r}, Next enabled, not flagged)")
        assert not accepted, (
            f"wizard accepts malformed email(s) {accepted} — no email-format validation on the "
            f"register wizard. Confirm with FE."
        )

    logger.info("RESULT: email-format validation enforced on the register wizard")


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_008(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_008: deal type is Referral (default) and persists to the summary.

    On this wizard build the deal type is fixed to **Referral** (a read-only badge —
    Reseller/Co-sell are NOT offered; see _009/_010, blocked). This verifies the
    referral deal type is captured on Deal info and persists to the Summary step
    after navigation. Referral implies the direct billing model (business rule); the
    UI shows the type as "Referral" (no separate "direct billing" label). No submit.
    """
    shell = make_partner_page(PartnerShellPage)
    wiz = make_partner_page(RegisterDealWizard)

    async with async_step("Setup: open the wizard; complete step 1"):
        await _open_deals(shell)
        await wiz.open()
        await wiz.fill_company("QA-AUTO Referral", unique_domain().split(".")[0])
        await wiz.select_first_country()
        await wiz.fill_contact("QA-AUTO Contact", unique_email())

    async with async_step(
        "[1/3] Deal info shows deal type = Referral (reseller/co-sell not offered)"
    ):
        await wiz.click_next()
        await wiz.wait_step("Step 2 of 3")
        assert await wiz.dialog().get_by_text("Referral", exact=False).first.is_visible(), (
            "Deal info must show the deal type 'Referral'"
        )
        assert await wiz.dialog().get_by_text("Reseller", exact=False).count() == 0, (
            "reseller must not be offered (deal type is fixed to Referral on this build)"
        )
        logger.info("CHECK deal type → OK (Referral; reseller/co-sell not offered in UI)")

    async with async_step("[2/3] Complete Deal info and continue to the Summary"):
        await wiz.pick_first_plan()
        await wiz.fill_seats(10)
        await wiz.pick_first_region()
        await wiz.pick_expected_close_date()
        await wiz.click_next()
        await wiz.wait_step("Step 3 of 3")

    async with async_step("[3/3] Summary persists deal type = Referral"):
        summary = wiz.dialog()
        assert await summary.get_by_text("Deal type", exact=False).first.is_visible(), (
            "summary must show the Deal type row"
        )
        assert await summary.get_by_text("Referral", exact=False).first.is_visible(), (
            "deal type must persist as 'Referral' on the summary after navigation"
        )
        logger.info("CHECK persist → OK (summary shows Deal type = Referral)")

    logger.info("RESULT: referral deal type captured and persisted to the summary")


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_011(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_011: the Summary step displays all entered data.

    Fills the wizard with known unique values (company / domain / contact name /
    email) plus deal info, reaches the Summary, and asserts every entered value is
    shown for review. Verified at the Summary step (pre-submit); no submit → no
    deal is created.
    """
    shell = make_partner_page(PartnerShellPage)
    wiz = make_partner_page(RegisterDealWizard)
    token = unique_domain().split(".")[0]  # unique subdomain label (no dots)
    company = f"QA-AUTO Summary {token}"
    domain = token
    contact_name = f"QA Contact {token}"
    contact_email = unique_email()

    async with async_step("Setup: fill the wizard (step 1 + Deal info) with known data"):
        await _open_deals(shell)
        await wiz.open()
        await wiz.fill_company(company, domain)
        await wiz.select_first_country()
        await wiz.fill_contact(contact_name, contact_email)
        await wiz.click_next()
        await wiz.wait_step("Step 2 of 3")
        await wiz.pick_first_plan()
        await wiz.fill_seats(10)
        await wiz.pick_first_region()
        await wiz.pick_expected_close_date()
        await wiz.click_next()
        await wiz.wait_step("Step 3 of 3")

    async with async_step("[1/2] Summary shows the entered COMPANY + CONTACT values"):
        summary = wiz.dialog()
        for field, value in (
            ("company name", company),
            ("domain", domain),
            ("contact name", contact_name),
            ("contact email", contact_email),
        ):
            assert await summary.get_by_text(value, exact=False).first.is_visible(), (
                f"summary must display the entered {field} ({value!r})"
            )
        logger.info("CHECK entered data → OK (company/domain/contact/email all shown on summary)")

    async with async_step("[2/2] Summary shows the DEAL section fields (type, plan, close date)"):
        for label in ("Deal type", "Referral", "Expected close date", "Plan source", "Country"):
            assert await summary.get_by_text(label, exact=False).first.is_visible(), (
                f"summary must show the '{label}' field"
            )
        logger.info("CHECK deal section → OK (Deal type=Referral, plan, close date, country shown)")

    logger.info("RESULT: the review Summary displays all entered data")


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_012(make_partner_page, partner_authenticated_page):
    """PARTNER_UI_MY_PIPELINE_012: a valid deal registration returns a success response within 2s.

    Performance: submits the full wizard with a valid (available) domain and asserts
    the register API responds 2xx within 2000 ms (measured from the request's own
    network timing — server + network round-trip, excluding UI render).

    Side-effect: submitting creates a real deal (no delete API — see _005 note). The
    created deal id is logged for manual lookup.
    """
    page = partner_authenticated_page
    shell = make_partner_page(PartnerShellPage)
    wiz = make_partner_page(RegisterDealWizard)

    result: dict = {}

    async def _on_resp(r):
        if r.request.method == "POST" and "/deals" in r.url:
            body = None
            try:
                body = await r.json()
            except Exception:  # noqa: BLE001 — best-effort
                body = None
            t = r.request.timing or {}
            dur = t.get("responseEnd", -1) - t.get("requestStart", -1)
            result.update(status=r.status, dur_ms=dur, body=body, url=r.url)

    page.on("response", lambda r: asyncio.create_task(_on_resp(r)))

    async with async_step("Setup: fill the full wizard with a valid (available) domain"):
        await _open_deals(shell)
        await wiz.open()
        await wiz.fill_company(
            f"QA-AUTO Perf {unique_domain().split('.')[0]}", unique_domain().split(".")[0]
        )
        await wiz.select_first_country()
        await wiz.fill_contact("QA-AUTO Contact", unique_email())
        await wiz.click_next()
        await wiz.wait_step("Step 2 of 3")
        await wiz.pick_first_plan()
        await wiz.fill_seats(10)
        await wiz.pick_first_region()
        await wiz.pick_expected_close_date()
        await wiz.click_next()
        await wiz.wait_step("Step 3 of 3")

    async with async_step("[1/2] Submit the deal"):
        await wiz.submit()
        await _wait_captured(page, result)
        assert result, "no register POST response was captured after submit"
        deal_id = (result.get("body") or {}).get("data", {}).get("_id")
        logger.info(
            "CHECK submit → OK (POST {} → {}, dealId={})", result["url"], result["status"], deal_id
        )
        assert result["status"] in (200, 201, 202), f"registration did not succeed: {result}"

    async with async_step("[2/2] Success response within 2 seconds"):
        dur = result.get("dur_ms", -1)
        assert dur > 0, f"could not measure the register response time (timing={dur})"
        logger.info("CHECK perf → response time {} ms (budget 2000 ms)", round(dur))
        assert dur < 2000, (
            f"register response took {round(dur)} ms (> 2000 ms budget) — performance gap; "
            f"re-run to rule out a staging blip before filing."
        )

    logger.info("RESULT: valid deal registration succeeded with a sub-2s response")


@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.mobile
async def test_partner_ui_my_pipeline_013(make_partner_page, partner_authenticated_page):
    """PARTNER_UI_MY_PIPELINE_013: the deal registration flow finishes under 90s on mobile.

    Performance/mobile: the ``mobile`` marker gives a 375×812 context (viewport + video
    match), so the full register wizard runs at mobile width; asserts the whole flow
    (open wizard → submitted) finishes under 90 seconds and the register succeeds.

    Side-effect: submitting creates a real deal (no delete API — see _005; deal id
    logged).
    """
    page = partner_authenticated_page
    shell = make_partner_page(PartnerShellPage)
    wiz = make_partner_page(RegisterDealWizard)

    result: dict = {}

    async def _on_resp(r):
        if r.request.method == "POST" and "/deals" in r.url:
            body = None
            try:
                body = await r.json()
            except Exception:  # noqa: BLE001 — best-effort
                body = None
            result.update(status=r.status, body=body, url=r.url, t_resp=time.perf_counter())

    page.on("response", lambda r: asyncio.create_task(_on_resp(r)))

    await _open_deals(shell)
    t0 = time.perf_counter()  # start of the registration flow

    async with async_step("[1/3] Mobile: open wizard + fill step 1"):
        await wiz.open()
        await wiz.fill_company(
            f"QA-AUTO Mobile {unique_domain().split('.')[0]}", unique_domain().split(".")[0]
        )
        await wiz.select_first_country()
        await wiz.fill_contact("QA-AUTO Contact", unique_email())
        await wiz.click_next()
        await wiz.wait_step("Step 2 of 3", hold_ms=200)

    async with async_step("[2/3] Mobile: fill Deal info → Summary"):
        await wiz.pick_first_plan()
        await wiz.fill_seats(10)
        await wiz.pick_first_region()
        await wiz.pick_expected_close_date()
        await wiz.click_next()
        await wiz.wait_step("Step 3 of 3", hold_ms=200)

    async with async_step("[3/3] Mobile: submit → flow finishes under 90s"):
        await wiz.submit()
        await _wait_captured(page, result)
        assert result, (
            "no register POST response captured after submit (mobile flow did not finish)"
        )
        deal_id = (result.get("body") or {}).get("data", {}).get("_id")
        assert result["status"] in (200, 201, 202), f"mobile registration did not succeed: {result}"
        elapsed = result["t_resp"] - t0
        logger.info(
            "CHECK mobile flow → OK (201, dealId={}, elapsed {:.1f}s, budget 90s)", deal_id, elapsed
        )
        assert elapsed < 90, f"mobile registration flow took {elapsed:.1f}s (> 90s budget)"

    logger.info("RESULT: mobile deal registration flow completed under 90 seconds")
