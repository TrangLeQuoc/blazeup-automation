"""Locators for the Partner Portal Commissions page (/commissions).

Verified against the live staging DOM (2026-07-27, channel-partner user). The page
shows 4 summary stat cards, a set of ledger status tabs (role="tab"), and a
commissions table with an empty-state when there are none.
"""


class CommissionsLocators:
    """Commissions page: summary cards + ledger tabs + table."""

    # Page-title READY_MARKER (in <main>).
    READY_MARKER = "Commissions"

    # The 4 summary stat cards (each shows a $ value).
    SUMMARY_CARDS = ("Pending Payout", "Paid YTD", "Total Earned", "Clawback Risk")

    # Ledger status tabs (role="tab").
    TABS = ("All", "Earned", "Pending", "Approved", "Paid", "Disputed", "Clawback")

    # Empty-state when the partner has no commissions yet.
    EMPTY_STATE_TEXT = "No commissions yet"

    # Loading spinner over the table while its data is fetched (Tailwind ring).
    LIST_SPINNER = "[class*='animate-spin'], [class*='border-t-transparent']"
