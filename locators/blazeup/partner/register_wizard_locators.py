"""Locators for the Partner Portal "Register a Deal" wizard (modal on /deals).

Verified live 2026-07-24. The wizard is a 3-step modal dialog opened by the
"Register a deal" CTA: Step 1 "Register company" (company info + primary contact),
Step 2 "Deal info", Step 3 "Summary". Inputs have no name/testid, so they are keyed
by their placeholder text (stable copy). Validation is enforced by DISABLING the
"Next" button until the step's required fields are filled (no inline error text).
"""


class RegisterWizardLocators:
    """Register-a-Deal wizard: dialog + step-1 fields + step controls."""

    DIALOG = "[role=dialog]"

    # Step 1 — Company info (required: name, domain, country).
    COMPANY_NAME = "input[placeholder='Acme Corporation']"
    # Domain placeholder is the bare subdomain label "acme" (changed from "acme.com"
    # 2026-08-04); the old selector matched 0 elements → fill timed out.
    DOMAIN = "input[placeholder='acme']"
    COUNTRY_TRIGGER_TEXT = "Select country"  # combobox trigger label

    # Step 1 — Primary contact (required: full name, email).
    CONTACT_NAME = "input[placeholder='Jane Doe']"
    CONTACT_EMAIL = "input[type='email']"

    # Step indicator text, e.g. "Step 1 of 3" / "Step 2 of 3" (in the dialog).
    STEP_RE = r"Step \d of \d"

    # A field label that appears ONLY on step 2 (Deal info) CONTENT — used to prove
    # the wizard actually advanced to Deal info, not just that the step counter
    # changed (the "Deal info" stepper label is present on every step).
    STEP2_CONTENT_MARKER = "Expected close date"
