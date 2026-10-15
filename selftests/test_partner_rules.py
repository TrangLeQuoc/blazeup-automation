"""utils.partner_rules mirrors requirement 2.2 — and never invents a rule it does not state.

The table is the single source tests read "what deal type should this partner get?" from,
so a silent edit (or a guessed mapping for a type the requirement leaves open) would make
every test that trusts it assert the wrong thing.
"""

import pytest

from utils.partner_rules import (
    DEAL_TYPE_LABELS,
    PARTNER_TYPE_RULES,
    RuleNotSpecified,
    expected_deal_type,
    rule_for,
)

# The four partner types the SA "Onboard New Partner" form offers (API value → label),
# matching requirement 2.2's four types.
_SA_TYPES = {
    "channel": "Channel",
    "referral": "Referral",
    "msp": "MSP",
    "system_integrator": "System Integrator",
}


def test_every_sa_partner_type_has_exactly_one_rule():
    assert set(PARTNER_TYPE_RULES) == set(_SA_TYPES)
    for api_type, label in _SA_TYPES.items():
        assert PARTNER_TYPE_RULES[api_type].api_type == api_type
        assert PARTNER_TYPE_RULES[api_type].sa_label == label


def test_billing_models_match_requirement_2_2():
    billing = {t: r.billing_model for t, r in PARTNER_TYPE_RULES.items()}
    assert billing == {
        "referral": "direct",
        "channel": "reseller",
        "system_integrator": "direct",
        "msp": "partner_managed",
    }


def test_channel_is_the_requirements_reseller_var_and_gets_reseller_deals():
    rule = expected_deal_type("channel")
    assert rule.requirement_type == "Reseller/VAR"
    assert (rule.deal_type, rule.deal_type_label) == ("reseller", "Reseller")


def test_referral_partners_get_referral_deals():
    rule = expected_deal_type("referral")
    assert (rule.deal_type, rule.deal_type_label) == ("referral", "Referral")


@pytest.mark.parametrize("api_type", ["msp", "system_integrator"])
def test_a_deal_type_the_requirement_does_not_state_is_never_guessed(api_type):
    assert rule_for(api_type).deal_type is None
    with pytest.raises(RuleNotSpecified, match="confirm with the PO"):
        expected_deal_type(api_type)


def test_every_defined_deal_type_is_a_real_deal_type():
    for rule in PARTNER_TYPE_RULES.values():
        assert rule.deal_type is None or rule.deal_type in DEAL_TYPE_LABELS
        assert rule.evidence, f"{rule.api_type}: say where the mapping comes from"


def test_lookup_is_case_insensitive_and_unknown_types_fail_loudly():
    assert rule_for(" Channel ").api_type == "channel"
    with pytest.raises(KeyError, match="not in requirement 2.2"):
        rule_for("reseller")  # a DEAL type, not a partner type — the classic mix-up
