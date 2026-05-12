"""Directory page object."""

from playwright.async_api import expect

from pages.base_page import BasePage
from locator.directory_ui import DirectorySelectors


class DirectoryPage(BasePage):
    """Page object for employee directory search and filters."""

    async def open(self) -> None:
        """Open the Directory module."""

        await self.goto("/directory")

    async def search_employee(self, name: str) -> None:
        """Search employees by name."""

        await self.fill(DirectorySelectors.SEARCH_INPUT, name)

    async def filter_by_department(self, department: str) -> None:
        """Filter employees by department."""

        dropdown = self.page.locator(DirectorySelectors.DEPARTMENT_FILTER).first
        await expect(dropdown).to_be_visible()
        if await dropdown.evaluate("node => node.tagName.toLowerCase() === 'select'"):
            await dropdown.select_option(label=department)
        else:
            await dropdown.click()
            await self.page.get_by_role("option", name=department).click()

    async def expect_employee_card(self, name: str) -> None:
        """Verify an employee card is visible by employee name."""

        await expect(self.page.locator(DirectorySelectors.EMPLOYEE_CARDS).filter(has_text=name).first).to_be_visible()
