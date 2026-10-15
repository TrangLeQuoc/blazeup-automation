"""Partner business rules — the ONE place tests read "what should this partner get?" from.

Source: requirement 2.2 "4 Partner Types" (docs/blazeup/partner_requirement.xlsx):

    Referral (billing: direct), Reseller/VAR (billing: reseller), SI (billing: direct),
    MSP (billing: partner_managed). Type selected at registration. Determines deal flows
    and billing models available.

Why this module exists: the register wizard fixes a partner's deal type FROM ITS PARTNER
TYPE. Until 2026-10-09 it showed a fixed "Referral" for every partner; from 2026-10-13 it
shows "Reseller" for a Channel partner (PAR-016854). Two UI TCs had hard-coded "Referral"
and broke without anything being wrong with the product. A test that needs "the deal type
this partner should see" asks this table instead of hard-coding a word.

Naming — three vocabularies for the same four types, kept side by side on purpose:
  * ``api_type``         — ``partner.type`` in the API (channel / referral / msp / system_integrator)
  * ``sa_label``         — what the SA UI shows (Onboard form + Directory TYPE column)
  * ``requirement_type`` — the name requirement 2.2 uses. NOTE: requirement "Reseller/VAR"
    is the SA's "Channel" (api ``channel``); there is no partner type called "Reseller".

A rule the requirement does not state is ``None`` — never guessed. Requirement 2.2 gives SI
and MSP a billing model but not a deal type, so ``expected_deal_type`` raises
``RuleNotSpecified`` for them and the caller reports the test BLOCKED (ask the PO), rather
than passing or failing on an invented expectation.
"""

from dataclasses import dataclass

# Deal types as the API names them (``dealType``) → how the wizard / deal list label them.
DEAL_TYPE_LABELS: dict[str, str] = {
    "referral": "Referral",
    "reseller": "Reseller",
    "co_sell": "Co-sell",
}


class RuleNotSpecified(LookupError):
    """The requirement does not define this rule — a test must not invent one."""


@dataclass(frozen=True)
class PartnerTypeRule:
    api_type: str
    sa_label: str
    requirement_type: str
    billing_model: str
    # The deal type the registration wizard fixes for this partner type (API value), or
    # None when the requirement does not say.
    deal_type: str | None
    # Where the mapping was confirmed, so a reader knows what is observed vs. only stated.
    evidence: str

    @property
    def deal_type_label(self) -> str | None:
        return DEAL_TYPE_LABELS[self.deal_type] if self.deal_type else None


PARTNER_TYPE_RULES: dict[str, PartnerTypeRule] = {
    "referral": PartnerTypeRule(
        api_type="referral",
        sa_label="Referral",
        requirement_type="Referral",
        billing_model="direct",
        deal_type="referral",
        evidence="requirement 2.2 + PRD §2.3 (not yet observed with a Referral partner)",
    ),
    "channel": PartnerTypeRule(
        api_type="channel",
        sa_label="Channel",
        requirement_type="Reseller/VAR",
        billing_model="reseller",
        deal_type="reseller",
        evidence=(
            "observed 2026-10-14 on PAR-016854: wizard badge RESELLER, Summary 'Reseller', "
            "POST /portal/deals dealType=reseller"
        ),
    ),
    "system_integrator": PartnerTypeRule(
        api_type="system_integrator",
        sa_label="System Integrator",
        requirement_type="SI",
        billing_model="direct",
        deal_type=None,
        evidence="requirement 2.2 gives the billing model only",
    ),
    "msp": PartnerTypeRule(
        api_type="msp",
        sa_label="MSP",
        requirement_type="MSP",
        billing_model="partner_managed",
        deal_type=None,
        evidence="requirement 2.2 gives the billing model only",
    ),
}


def rule_for(api_type: str) -> PartnerTypeRule:
    """The rule for a partner's ``type`` as the API returns it."""
    try:
        return PARTNER_TYPE_RULES[(api_type or "").strip().lower()]
    except KeyError:
        raise KeyError(
            f"unknown partner type {api_type!r} — not in requirement 2.2 "
            f"({sorted(PARTNER_TYPE_RULES)}). Add it to utils/partner_rules.py once the "
            "requirement defines it."
        ) from None


def expected_deal_type(api_type: str) -> PartnerTypeRule:
    """The rule for ``api_type``, guaranteed to define a deal type.

    Raises ``RuleNotSpecified`` when requirement 2.2 does not say which deal type this
    partner type gets — the caller should report BLOCKED, never guess.
    """
    rule = rule_for(api_type)
    if rule.deal_type is None:
        raise RuleNotSpecified(
            f"requirement 2.2 does not define the deal type for a {rule.sa_label} partner "
            f"({rule.api_type}) — confirm with the PO before asserting one"
        )
    return rule
