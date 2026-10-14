"""Partner Portal — My Pipeline (Deals) page (UI, Layer-B content).

Per-page CONTENT tests for the Deal Pipeline page (/deals). Navigation + shell
readiness come from PartnerShellPage; page-specific widgets are read via DealsPage.

    PARTNER_UI_MY_PIPELINE_014 — open my pipeline: all stage controls + their deal
                                 counts are visible (works with an empty pipeline).
    _024 — clicking a deal row opens the Deal Detail drawer.
    _025 — the Filter popover opens with the filter builder.
    _032 — deals table renders rows + the expected columns.
    _033 — a stage control filters the list to that status (count matches).
    _034 — the Deal Detail drawer shows the clicked deal's info sections.
    _035 — pagination: page 2 loads a different set of deals.
    _036 — each row's DEAL TYPE / ESTIMATED ACV / STATUS are well-formed.
    _037 — a zero-count stage shows the 'No deals found' empty state.

_024/_025 + _032-_037 need a partner WITH deals; they run against the shared seeded
partner (102 deals live 2026-10-02). They became writeable only after the BE fixed
the deals-list endpoint (was 400 "Invalid id: 'pro-v1'" on legacy-slug plan refs,
which had blocked the whole deal-list/detail family — _024/_025 included).
"""

import re

import pytest
from loguru import logger

from locators.blazeup.partner.deals_locators import DealsLocators
from pages.blazeup.partner.deals_page import DealsPage
from pages.blazeup.partner.partner_shell_page import PartnerShellPage
from utils.log_helper import async_step

# Deal-type / status vocab for the typed-cell checks (_036). Case-insensitive.
_DEAL_TYPES = ("referral", "reseller", "co-sell", "cosell", "co sell")
_STATUSES = ("pending", "approved", "won", "lost", "expired", "in progress", "registered")


async def _open_deals(make_partner_page):
    """Open the Deals page via the shell and wait for the list to settle."""
    shell = make_partner_page(PartnerShellPage)
    deals = make_partner_page(DealsPage)
    await shell.open("deals")
    await shell.wait_ready("deals")
    await deals.wait_list_settled()
    return deals


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_014(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_014: open My Pipeline — all deal stages and their counts are visible.

    Opens the Deals page via the shell, then asserts the pipeline shows every stage
    control (All/Pending/Approved/In Progress/Won/Lost/Expired) each with a numeric deal
    count, plus the pipeline summary and the Register CTA. Read-only: works with an empty
    pipeline (counts may be 0) — it verifies the stages RENDER, not any specific data.

    The stages are rendered as BUTTONS labelled "<Stage> <count>" (the FE moved off
    role=tab and added "In Progress" — verified live 2026-10-08), so they are read through
    ``stage_button``/``stage_button_count``, not the old role=tab locator.
    """
    shell = make_partner_page(PartnerShellPage)
    deals = make_partner_page(DealsPage)

    async with async_step("Setup: open the Deals page (My Pipeline) and let it settle"):
        await shell.open("deals")
        await shell.wait_ready("deals")  # marker "Deal Pipeline" in <main>; fast-fail on panel
        await deals.wait_list_settled()  # deals-list fetch done + spinner gone (stable page)

    async with async_step("[1/3] Every pipeline stage control is visible"):
        for stage in DealsPage.STAGES:
            control = deals.stage_button(stage)
            assert await control.is_visible(), f"stage '{stage}' is not visible on the pipeline"
        logger.info("CHECK stages → OK (visible: {})", ", ".join(DealsPage.STAGES))

    async with async_step("[2/3] Every stage control shows a numeric deal count"):
        counts: dict[str, int] = {}
        for stage in DealsPage.STAGES:
            count = await deals.stage_button_count(stage)
            assert count is not None, f"stage '{stage}' shows no numeric count"
            assert count >= 0, f"stage '{stage}' count must be >= 0, got {count}"
            counts[stage] = count
        logger.info("CHECK counts → OK ({})", counts)

    async with async_step("[3/3] Pipeline summary + Register CTA are visible"):
        assert await deals.summary().is_visible(), (
            "pipeline summary ('… deals in your pipeline') is not visible"
        )
        assert await deals.register_button().is_visible(), "'Register a deal' CTA is not visible"
        logger.info("CHECK controls → OK (summary + Register a deal visible)")

    logger.info("RESULT: My Pipeline shows all 6 stages with counts {}", counts)


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_032(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_032: My Pipeline deals table renders rows + the expected columns.

    On a partner that HAS deals, the table shows the documented columns and at least
    one data row, and the first row carries a Deal ID and a STATUS. Proves the
    deals-list renders (the regression that _024/_025 were blocked on).
    """
    deals = await _open_deals(make_partner_page)

    async with async_step("[1/3] The deals table shows the expected column headers"):
        headers = [h.upper() for h in await deals.column_headers()]
        for col in ("DEAL ID", "DOMAIN", "DEAL TYPE", "ESTIMATED ACV", "STATUS"):
            assert col in headers, f"column '{col}' missing from headers {headers}"
        logger.info("CHECK columns → OK ({})", headers)

    async with async_step("[2/3] At least one deal row is rendered"):
        n = await deals.data_row_count()
        assert n > 0, "deals table rendered no rows (empty state) — the partner should have deals"
        logger.info("CHECK rows → OK ({} rows on page 1)", n)

    async with async_step("[3/3] The first row carries a Deal ID and a STATUS value"):
        deal_id = await deals.row_cell(0, "DEAL ID")
        status = await deals.row_status(0)
        assert deal_id.strip(), "first row has no Deal ID"
        assert status.strip(), "first row has no STATUS"
        logger.info("RESULT: list renders — row0 id={!r} status={!r}", deal_id, status)


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_033(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_033: a stage control filters the list to that status.

    Picks a non-'All' stage whose count is between 1 and one page (<=20), clicks it,
    and asserts the rendered rows match: row count equals the stage count and every
    row's STATUS is that stage.
    """
    deals = await _open_deals(make_partner_page)

    async with async_step("[1/3] Pick a non-empty stage that fits on one page (1..20 deals)"):
        target, target_count = None, None
        for stage in DealsLocators.STAGE_BUTTONS[1:]:
            c = await deals.stage_button_count(stage)
            if c is not None and 1 <= c <= 20:
                target, target_count = stage, c
                break
        assert target, "no stage with 1..20 deals to assert a single-page filter against"
        logger.info("CHECK pick → stage '{}' (count={})", target, target_count)

    async with async_step("[2/3] Click the stage and the list shows exactly its deals"):
        await deals.click_stage(target)
        # Count AND statuses: a count match alone may still be the previous (All) view.
        assert await deals.wait_stage_applied(target, target_count), (
            f"stage '{target}' tab says {target_count} but the table did not switch to "
            f"{target_count} '{target}' rows ({await deals.data_row_count()} deal rows rendered)"
        )
        n = target_count
        logger.info("CHECK count → OK ({} rows)", n)

    async with async_step("[3/3] Every rendered row has that stage's STATUS"):
        for i in range(n):
            st = (await deals.row_status(i)).lower()
            assert target.lower() in st, f"row {i} status {st!r} does not match stage '{target}'"
        logger.info("RESULT: stage '{}' filter narrows the list correctly", target)


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_024(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_024: clicking a deal row opens the Deal Detail drawer.

    Was BLOCKED by the deals-list 400 defect (no rows rendered). Now: click the first
    row → the 'Deal Detail' drawer opens in place (no route change).
    """
    deals = await _open_deals(make_partner_page)

    async with async_step("Setup: there is at least one deal row to open"):
        assert await deals.data_row_count() > 0, "no deal rows to open"

    async with async_step("[1/2] Click the first deal row → the Deal Detail drawer opens"):
        url_before = deals.page.url
        await deals.open_detail(0)
        assert await deals.detail_heading().is_visible(), "'Deal Detail' drawer did not open"
        logger.info("CHECK drawer → OK (Deal Detail visible)")

    async with async_step("[2/2] The drawer opens in place (URL stays on /deals)"):
        assert deals.page.url == url_before, (
            f"expected an in-place drawer, but the URL changed {url_before} → {deals.page.url}"
        )
        logger.info("RESULT: row click opens the Deal Detail drawer in place")


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_025(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_025: the Filter popover opens with the filter builder.

    Was BLOCKED together with _024. The portal has no free-text search box; filtering
    is a radix popover 'builder' (a field combobox defaulting to Deal Type + an
    'Add Filter' control). This verifies that entry point opens and is interactive.
    """
    deals = await _open_deals(make_partner_page)

    async with async_step("[1/2] Click Filter → the filter popover opens"):
        popover = await deals.open_filter()
        assert await popover.is_visible(), "Filter popover did not open"
        logger.info("CHECK popover → OK (open)")

    async with async_step("[2/2] The popover exposes the filter builder ('Add Filter' control)"):
        assert (
            await popover.get_by_text(DealsLocators.FILTER_ADD_BUTTON, exact=False).count() >= 1
        ), "'Add Filter' control not found in the filter popover"
        logger.info("RESULT: Filter popover exposes the builder (Add Filter present)")


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_034(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_034: the Deal Detail drawer shows the clicked deal's info.

    Opens the first deal's detail and asserts the drawer carries its info sections
    (DEAL INFO + COMPANY INFO) and the row's company/domain text appears inside it —
    i.e. the drawer reflects the deal that was clicked, not a blank shell.
    """
    deals = await _open_deals(make_partner_page)

    async with async_step("Setup: capture the first row's DOMAIN/company, then open its detail"):
        assert await deals.data_row_count() > 0, "no deal rows to open"
        row_domain = await deals.row_cell(0, "DOMAIN")
        await deals.open_detail(0)

    async with async_step("[1/2] The drawer shows the DEAL INFO and COMPANY INFO sections"):
        for section in DealsLocators.DETAIL_SECTIONS:
            assert await deals.detail_section(section).is_visible(), (
                f"detail drawer is missing the '{section}' section"
            )
        logger.info("CHECK sections → OK ({})", ", ".join(DealsLocators.DETAIL_SECTIONS))

    async with async_step(
        "[2/2] The drawer reflects the clicked deal (its company/domain text appears)"
    ):
        # The DOMAIN cell holds company + contact; assert a meaningful token from it
        # shows in the drawer.
        token = next((t for t in re.split(r"\s{2,}|\t|\n", row_domain) if len(t.strip()) >= 3), "")
        assert token, f"could not derive a company token from row domain {row_domain!r}"
        drawer = deals.detail_drawer()
        assert await drawer.get_by_text(token.strip(), exact=False).count() >= 1, (
            f"clicked deal's token {token.strip()!r} not found in the detail drawer"
        )
        logger.info("RESULT: detail drawer reflects the clicked deal ({!r})", token.strip())


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_037(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_037: a zero-count stage shows the 'No deals found' empty state.

    Picks a stage whose tab count is 0 (e.g. Lost/Expired), clicks it, and asserts the
    table renders no rows and the empty-state message appears.
    """
    deals = await _open_deals(make_partner_page)

    async with async_step("[1/3] Find a stage with a zero deal count"):
        empty_stage = None
        for stage in DealsLocators.STAGE_BUTTONS[1:]:
            if (await deals.stage_button_count(stage)) == 0:
                empty_stage = stage
                break
        assert empty_stage, "no zero-count stage available to assert the empty state"
        logger.info("CHECK pick → zero stage '{}'", empty_stage)

    async with async_step("[2/3] Switching to it shows the 'No deals found' empty state"):
        await deals.click_stage(empty_stage)
        assert await deals.wait_empty_state(), (
            f"stage '{empty_stage}' did not show the 'No deals found' empty state"
        )
        logger.info("CHECK empty state → OK (visible)")

    async with async_step("[3/3] No deal data rows are listed under the empty stage"):
        n = await deals.data_row_count()
        assert n == 0, f"stage '{empty_stage}' is 0 but {n} deal row(s) rendered"
        logger.info(
            "RESULT: zero-count stage '{}' shows the empty state, no data rows", empty_stage
        )


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_035(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_035: pagination — page 2 loads a different set of deals.

    Requires more than one page of deals (All count > one page). Captures page 1's
    first Deal ID, jumps to page 2, and asserts rows still render and the first Deal ID
    changed (a new page actually loaded).
    """
    deals = await _open_deals(make_partner_page)

    async with async_step("Setup: ensure there is more than one page of deals"):
        total = await deals.stage_button_count("All")
        if await deals.page_input().count() == 0 or (total is not None and total <= 20):
            pytest.skip(f"BLOCKED: only {total} deals — pagination not exercised (needs > 1 page)")
        page1_id = await deals.row_cell(0, "DEAL ID")
        logger.info("SETUP: total={} page1 first id={!r}", total, page1_id)

    async with async_step("[1/2] Jump to page 2 → a new page of deals loads"):
        await deals.go_to_page(2)
        assert await deals.wait_first_deal_changed(page1_id), (
            f"page 2 first id still {page1_id!r} — the page did not change"
        )
        assert await deals.data_row_count() > 0, "page 2 rendered no rows"
        logger.info("CHECK page2 → OK ({} rows)", await deals.data_row_count())

    async with async_step("[2/2] Page 2's first deal differs from page 1"):
        page2_id = await deals.row_cell(0, "DEAL ID")
        assert page2_id != page1_id, (
            f"page 2 first id {page2_id!r} == page 1 {page1_id!r} — page did not change"
        )
        logger.info("RESULT: pagination works (p1 {!r} → p2 {!r})", page1_id, page2_id)


@pytest.mark.ui
@pytest.mark.regression
async def test_partner_ui_my_pipeline_036(make_partner_page):
    """PARTNER_UI_MY_PIPELINE_036: each deal row's DEAL TYPE / ESTIMATED ACV / STATUS are well-formed.

    Reads the first few rows and checks the typed columns: DEAL TYPE is a known deal
    type, ESTIMATED ACV carries a currency amount, and STATUS is a known pipeline
    status. All rows are checked (failures collected) so one bad row never hides others.
    """
    deals = await _open_deals(make_partner_page)
    gaps: list[str] = []

    async with async_step("Setup: there are rows to inspect"):
        n = min(await deals.data_row_count(), 5)
        assert n > 0, "no deal rows to inspect"

    for i in range(n):
        async with async_step(
            f"[{i + 1}/{n}] Row {i}: DEAL TYPE / ESTIMATED ACV / STATUS are valid", soft=gaps
        ):
            dtype = (await deals.row_cell(i, "DEAL TYPE")).lower()
            acv = await deals.row_cell(i, "ESTIMATED ACV")
            status = (await deals.row_status(i)).lower()
            if not any(t in dtype for t in _DEAL_TYPES):
                gaps.append(f"row {i}: DEAL TYPE {dtype!r} not a known deal type")
            if not re.search(r"\d", acv):
                gaps.append(f"row {i}: ESTIMATED ACV {acv!r} has no amount")
            if not any(s in status for s in _STATUSES):
                gaps.append(f"row {i}: STATUS {status!r} not a known status")
            logger.info("CHECK row {} → type={!r} acv={!r} status={!r}", i, dtype, acv, status)

    assert not gaps, "Malformed deal rows:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: {} rows have well-formed type/ACV/status", n)
