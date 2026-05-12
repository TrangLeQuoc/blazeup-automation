"""Selectors for the directory page."""


class DirectorySelectors:
    """Directory page selectors."""

    SEARCH_INPUT = "input[type='search'], input[placeholder*='search' i]"
    DEPARTMENT_FILTER = (
        "select[name*='department' i], "
        "[role='combobox']:has-text('Department')"
    )
    EMPLOYEE_CARDS = "[data-testid='employee-card'], .employee-card"

