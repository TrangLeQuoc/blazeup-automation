"""Expense page object."""

from pages.base_page import BasePage
from locator.expense_ui import ExpenseSelectors


class ExpensePage(BasePage):
    """Page object for expense module navigation and smoke assertions."""

    async def open(self) -> None:
        """Open the Expenses module."""

        await self.goto("/expenses")

    async def start_new_expense(self) -> None:
        """Open the create expense flow."""

        await self.click(ExpenseSelectors.NEW_EXPENSE_BUTTON)
