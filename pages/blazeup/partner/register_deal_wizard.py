"""Partner Portal "Register a Deal" wizard page object (modal on /deals).

Drives the 3-step registration modal. Step 1 ("Register company") captures company
info + primary contact; the "Next" button is DISABLED until the step's required
fields are filled (the wizard's validation mechanism — there is no inline error
text). Navigation to /deals + shell readiness come from PartnerShellPage.
"""

import contextlib
import re

from loguru import logger
from playwright.async_api import Locator
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import expect as pw_expect

from locators.blazeup.partner.register_wizard_locators import RegisterWizardLocators as L
from pages.base_page import BasePage

# Inline warning shown when the entered domain is already reserved (active deal /
# account). Matched by its wording (no stable selector on this build).
_DOMAIN_WARNING_RE = re.compile(r"reserved|active deal|conflict", re.IGNORECASE)


class RegisterDealWizard(BasePage):
    """Actions for the Register-a-Deal wizard (step 1 focus)."""

    def dialog(self) -> Locator:
        return self.page.locator(L.DIALOG).first

    async def open(self, timeout: int = 15_000, field_timeout: int = 45_000) -> None:
        """Open the wizard via the 'Register a deal' CTA and wait until it is fillable.

        Waits for the dialog AND for the first step-1 field (company name) to be
        visible/editable before returning — the modal shell can render before its
        form MFE hydrates, so without this the caller's first ``fill`` races the
        hydration and times out under slow cold-loads (the register-wizard flaky).
        ``field_timeout`` is generous to absorb staging cold-loads.
        """
        await self.page.get_by_role("button", name="Register a deal").first.click()
        await self.dialog().wait_for(state="visible", timeout=timeout)
        await self.page.locator(L.COMPANY_NAME).wait_for(state="visible", timeout=field_timeout)
        logger.log("STEP", "Opened Register-a-Deal wizard")

    async def step_text(self) -> str:
        """Return the step indicator, e.g. 'Step 1 of 3' (empty if not found)."""
        m = re.search(L.STEP_RE, await self.dialog().inner_text())
        return m.group(0) if m else ""

    async def wait_step(self, expected: str, hold_ms: int = 1000, timeout: int = 10_000) -> None:
        """Wait until the wizard shows *expected* (e.g. 'Step 2 of 3'), then hold briefly.

        Step transitions are client-side and instant, so without this the assertions
        fire in the same frame and the step is barely visible in the recorded video.
        Waiting for the indicator makes the assertion robust; the short hold makes each
        step actually visible on the run video.
        """
        await pw_expect(self.dialog()).to_contain_text(expected, timeout=timeout)
        await self.page.wait_for_timeout(hold_ms)

    async def fill_company(self, name: str | None, domain: str) -> None:
        """Fill company name (skip when name is None) + domain."""
        if name is not None:
            await self.page.locator(L.COMPANY_NAME).fill(name)
        await self.page.locator(L.DOMAIN).fill(domain)

    async def fill_domain(self, value: str) -> None:
        """Set the Domain field and blur it (to trigger any field-level validation)."""
        d = self.page.locator(L.DOMAIN)
        await d.fill(value)
        await d.blur()

    async def domain_aria_invalid(self) -> bool:
        """True if the Domain field is flagged invalid (aria-invalid='true')."""
        return (await self.page.locator(L.DOMAIN).get_attribute("aria-invalid")) == "true"

    async def wait_domain_warning(self, timeout: int = 8_000) -> str:
        """Wait for + return the inline 'domain reserved / active deal' warning text.

        The Domain field triggers an async ``check-domain`` call on blur; a reserved
        domain shows an inline warning. Returns "" if no warning appears within
        *timeout* (i.e. the domain is available).
        """
        loc = self.dialog().get_by_text(_DOMAIN_WARNING_RE).first
        with contextlib.suppress(PlaywrightTimeoutError):
            await loc.wait_for(state="visible", timeout=timeout)
        if await loc.count() and await loc.is_visible():
            return " ".join((await loc.inner_text()).split())
        return ""

    async def domain_warning_text(self) -> str:
        """Return the current inline domain warning text ("" if none) — no waiting."""
        loc = self.dialog().get_by_text(_DOMAIN_WARNING_RE).first
        if await loc.count() and await loc.is_visible():
            return " ".join((await loc.inner_text()).split())
        return ""

    async def select_first_country(self) -> None:
        """Open the Country combobox and pick the first option (any valid country)."""
        await self.page.get_by_text(L.COUNTRY_TRIGGER_TEXT, exact=False).first.click()
        await self.page.get_by_role("option").first.click()

    async def fill_contact(self, name: str, email: str) -> None:
        """Fill the primary-contact full name + email."""
        await self.page.locator(L.CONTACT_NAME).fill(name)
        await self.page.locator(L.CONTACT_EMAIL).first.fill(email)

    async def fill_email(self, value: str) -> None:
        """Set only the primary-contact email and blur it (to trigger validation)."""
        e = self.page.locator(L.CONTACT_EMAIL).first
        await e.fill(value)
        await e.blur()

    async def email_aria_invalid(self) -> bool:
        """True if the contact-email field is flagged invalid (aria-invalid='true')."""
        return (
            await self.page.locator(L.CONTACT_EMAIL).first.get_attribute("aria-invalid")
        ) == "true"

    async def deal_info_visible(self) -> bool:
        """True if step 2 (Deal info) CONTENT is rendered (a step-2-only field is visible).

        Checks a field that appears only on the Deal-info content (not the always-
        present 'Deal info' stepper label), to prove the wizard truly advanced.
        """
        return (
            await self.dialog().get_by_text(L.STEP2_CONTENT_MARKER, exact=False).first.is_visible()
        )

    # -- step 2 (Deal info) fields ------------------------------------------

    async def pick_first_plan(self) -> None:
        """Open the Plan dropdown and pick the first plan (billing cycle auto-sets)."""
        await self.dialog().get_by_text("Select a plan", exact=False).first.click()
        await self.page.get_by_role("option").first.click()

    async def fill_seats(self, amount: int = 10) -> None:
        """Fill the granted-seats amount."""
        await self.page.locator("input[placeholder='Enter the amount']").fill(str(amount))

    async def pick_first_region(self) -> None:
        """Open the Region dropdown (enabled after a plan is chosen) and pick the first."""
        await self.dialog().get_by_text("Select a region", exact=False).first.click()
        await self.page.get_by_role("option").first.click()

    async def pick_expected_close_date(self) -> None:
        """Pick an expected close date in the NEXT month (all days future/enabled).

        Opens the calendar, advances one month, and clicks day 15 (a mid-month day
        that always exists and is in the future).
        """
        await self.dialog().get_by_text("Select expected close date", exact=False).first.click()
        await self.page.get_by_role("button", name="Go to the Next Month").first.click()
        await self.page.wait_for_timeout(400)
        await self.page.locator("[role=dialog] button", has_text=re.compile(r"^15$")).first.click()

    async def submit(self) -> str:
        """On the summary step, click the primary submit/confirm button. Returns its label."""
        for name in ("Submit", "Register deal", "Confirm", "Register", "Finish", "Create deal"):
            btn = self.dialog().get_by_role("button", name=name, exact=False).first
            if await btn.count() and await btn.is_visible() and not await btn.is_disabled():
                await btn.click()
                return name
        raise AssertionError("no submit/confirm button found on the wizard summary step")

    def next_button(self) -> Locator:
        return self.dialog().get_by_role("button", name="Next").first

    def back_button(self) -> Locator:
        return self.dialog().get_by_role("button", name="Back").first

    async def next_enabled(self) -> bool:
        """True when the 'Next' button is enabled (step's required fields satisfied)."""
        return not await self.next_button().is_disabled()

    async def click_next(self) -> None:
        await self.next_button().click()

    async def click_back(self) -> None:
        await self.back_button().click()

    async def company_value(self) -> str:
        """Current value of the company-name input (to prove data is preserved)."""
        return await self.page.locator(L.COMPANY_NAME).input_value()

    async def domain_value(self) -> str:
        """Current value of the Domain input."""
        return await self.page.locator(L.DOMAIN).input_value()

    async def contact_name_value(self) -> str:
        """Current value of the primary-contact full-name input."""
        return await self.page.locator(L.CONTACT_NAME).input_value()

    async def contact_email_value(self) -> str:
        """Current value of the primary-contact email input."""
        return await self.page.locator(L.CONTACT_EMAIL).first.input_value()

    async def country_selected(self) -> bool:
        """True once a country is chosen (the 'Select country' placeholder is gone)."""
        return await self.dialog().get_by_text(L.COUNTRY_TRIGGER_TEXT, exact=False).count() == 0
