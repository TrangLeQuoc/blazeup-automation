"""Expense API client."""

from pydantic import BaseModel, ConfigDict

from api.base_client import BaseClient


class ExpenseResponse(BaseModel):
    """Expense response schema."""

    model_config = ConfigDict(extra="allow")

    id: str | int
    amount: float | int | None = None
    status: str | None = None


class ExpenseClient(BaseClient):
    """Client for expense endpoints."""

    async def list_expenses(self, expected_status: int = 200) -> object:
        """Return expenses for the current user."""

        return await self.get("/expenses", expected_status=expected_status)

    async def get_expense(self, expense_id: str | int, expected_status: int = 200) -> ExpenseResponse:
        """Return a single expense by id."""

        return await self.get(f"/expenses/{expense_id}", expected_status=expected_status, schema=ExpenseResponse)

