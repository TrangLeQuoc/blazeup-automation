"""SA Audit Log API — read-only audit trail (service: sa-partners-api).

Maps to the Partner Platform test plan: PARTNER_API_AUDIT_LOG_*.

``GET /sa-partners-api/v1/sa/audit-logs`` returns the SA audit trail envelope
``{statusCode, data[], total, page, limit, message}``. Read-only — these tests
create nothing and need no cleanup (and no billing plan, so no sa-plans dependency).
"""

import pytest
from loguru import logger

from utils.log_helper import async_step

# Keys that must never appear on an audit entry (no credential material in the trail).
_SENSITIVE = ("password", "token", "secret", "pwd", "credential")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_audit_log_001(sa_partners_client):
    """PARTNER_API_AUDIT_LOG_001: SA lists audit log entries - paginated, filterable, well-formed.

    Read-only contract on ``GET /sa-partners-api/v1/sa/audit-logs``: returns HTTP
    200 with the envelope ``{statusCode, data[], total, message}``, honours
    pagination (page size never exceeds the requested limit), each entry carries the
    required audit fields with the right types (id/action/category/severity/createdAt
    plus actor/resource objects), leaks no sensitive field, and a ``category`` filter
    returns only matching entries.
    """
    limit = 5
    async with async_step(f"[1/4] GET /v1/sa/audit-logs (page=1, limit={limit})"):
        resp = await sa_partners_client.list_audit_logs(limit=limit, page=1)
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert isinstance(resp.data, list), "`data` must be a list"
        assert resp.total is not None and resp.total >= 0, "`total` must be a non-negative integer"
        assert resp.message, "`message` should be present"
        logger.info("CHECK envelope → OK (total={}, returned={})", resp.total, len(resp.data))

    async with async_step("[2/4] Verify pagination (page size <= limit)"):
        assert len(resp.data) <= limit, (
            f"page size {len(resp.data)} must not exceed requested limit {limit}"
        )
        logger.info("CHECK pagination → OK ({} <= {})", len(resp.data), limit)

    if not resp.data:
        logger.warning("CHECK schema/filter — SKIPPED: audit log is empty on this environment")
        logger.info("RESULT: audit-log list contract verified (empty dataset)")
        return

    async with async_step("[3/4] Verify each entry's schema + no sensitive field leaked"):
        for e in resp.data:
            assert isinstance(e, dict) and e, "each entry must be a non-empty object"
            assert e.get("_id") or e.get("id"), "entry must carry an id"
            assert isinstance(e.get("action"), str) and e.get("action"), (
                "action must be a non-empty string"
            )
            assert isinstance(e.get("category"), str) and e.get("category"), (
                "category must be a non-empty string"
            )
            assert isinstance(e.get("severity"), str) and e.get("severity"), (
                "severity must be a non-empty string"
            )
            assert e.get("createdAt"), "entry must carry createdAt"
            assert isinstance(e.get("actor"), dict), "actor must be an object"
            assert isinstance(e.get("resource"), dict), "resource must be an object"
            leaked = [k for k in e if any(s in str(k).lower() for s in _SENSITIVE)]
            assert not leaked, f"audit entry must not expose sensitive keys: {leaked}"
        logger.info("CHECK schema → OK ({} entries well-formed, no sensitive leak)", len(resp.data))

    async with async_step("[4/4] Verify a category filter returns only matching entries"):
        category = resp.data[0].get("category")
        filtered = await sa_partners_client.list_audit_logs(limit=10, category=category)
        assert filtered.status_code == 200, "filtered list must return 200"
        assert all(x.get("category") == category for x in filtered.data), (
            f"category filter must return only '{category}' entries"
        )
        logger.info("CHECK filter → OK (category='{}' → {} matching)", category, len(filtered.data))

    logger.info("RESULT: audit-log list verified (total={}, paginated, filterable)", resp.total)


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_audit_log_005(sa_partners_client):
    """PARTNER_API_AUDIT_LOG_005: list audit logs with invalid pagination/filter - graceful 4xx, never 5xx.

    Negative counterpart of _001. Invalid pagination and out-of-enum / bad-format
    filters must be rejected with 4xx (never 5xx) + a clear message. A logically
    valid but empty range (dateFrom > dateTo) is handled gracefully (200, empty) —
    not an error. All cases run (failures collected) so one gap never hides others.
    """
    # (label, query params, expected message hint)
    cases = [
        ("page=0", {"page": 0, "limit": 5}, "page must not be less than 1"),
        ("page=-1", {"page": -1, "limit": 5}, "page must not be less than 1"),
        ("limit=0", {"limit": 0}, "limit must not be less than 1"),
        ("limit=-5", {"limit": -5}, "limit must not be less than 1"),
        ("limit over max", {"limit": 999999}, "limit must not be greater than 100"),
        ("page non-numeric", {"page": "abc", "limit": 5}, "page must be an integer"),
        ("invalid severity", {"limit": 5, "severity": "bogus"}, "severity must be one of"),
        ("invalid category", {"limit": 5, "category": "bogus"}, "category must be one of"),
        ("invalid actorType", {"limit": 5, "actorType": "bogus"}, "actortype must be one of"),
        ("bad dateFrom", {"limit": 5, "dateFrom": "31-12-2026"}, "datefrom must be a valid iso"),
        ("bad dateTo", {"limit": 5, "dateTo": "not-a-date"}, "dateto must be a valid iso"),
    ]
    total_steps = len(cases) + 1
    gaps: list[str] = []
    for idx, (label, params, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{total_steps}] Reject invalid list: {label}"):
            r = await sa_partners_client.raw_list_audit_logs(expected_status=None, **params)
            msg = str(r.json().get("message") or "")
            if 400 <= r.status_code < 500 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    async with async_step(f"[{total_steps}/{total_steps}] Empty-but-valid range is graceful"):
        r = await sa_partners_client.raw_list_audit_logs(
            limit=5, dateFrom="2026-12-31", dateTo="2026-01-01"
        )
        if r.status_code < 500:
            logger.info("CHECK dateFrom>dateTo → OK (graceful {}, no 5xx)", r.status_code)
        else:
            gaps.append(f"dateFrom>dateTo: status={r.status_code}")
            logger.error("CHECK dateFrom>dateTo → FAIL (5xx {})", r.status_code)

    assert not gaps, "audit-log list negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: all invalid audit-log list attempts rejected (4xx, never 5xx)")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_audit_log_002(sa_partners_client):
    """PARTNER_API_AUDIT_LOG_002: SA retrieves audit-log KPI stats - 24h counts + chain integrity.

    Read-only contract on ``GET /sa-partners-api/v1/sa/audit-logs/stats``: returns
    HTTP 200 with the envelope ``{statusCode, data{}, message}`` where ``data``
    carries the 24h KPI counters (totalEvents24h, criticalEvents24h, warnings24h,
    uniqueActors24h) as non-negative ints plus ``chainIntegrityPct`` as a 0..100
    percentage. Counters are internally consistent (critical/warnings/uniqueActors
    never exceed the total). The endpoint takes no params, so there is no
    invalid-input negative counterpart.
    """
    counters = ("totalEvents24h", "criticalEvents24h", "warnings24h", "uniqueActors24h")

    async with async_step("[1/3] GET /v1/sa/audit-logs/stats"):
        resp = await sa_partners_client.get_audit_log_stats()
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        assert resp.message, "`message` should be present"
        assert isinstance(resp.data, dict) and resp.data, "`data` must be a non-empty object"
        logger.info("CHECK envelope → OK (data keys={})", sorted(resp.data))

    async with async_step("[2/3] Verify KPI fields present with correct types"):
        d = resp.data
        for f in counters:
            v = d.get(f)
            assert isinstance(v, int) and not isinstance(v, bool), f"{f} must be an int, got {v!r}"
            assert v >= 0, f"{f} must be non-negative, got {v}"
        pct = d.get("chainIntegrityPct")
        assert isinstance(pct, (int, float)) and not isinstance(pct, bool), (
            f"chainIntegrityPct must be numeric, got {pct!r}"
        )
        assert 0 <= pct <= 100, f"chainIntegrityPct must be a 0..100 percentage, got {pct}"
        logger.info("CHECK fields → OK (counters ints ≥0, chainIntegrityPct={} in 0..100)", pct)

    async with async_step("[3/3] Verify the counters are internally consistent"):
        d = resp.data
        total = d["totalEvents24h"]
        assert d["criticalEvents24h"] <= total, "critical 24h cannot exceed total 24h"
        assert d["warnings24h"] <= total, "warnings 24h cannot exceed total 24h"
        assert d["uniqueActors24h"] <= total, "unique actors 24h cannot exceed total events 24h"
        logger.info("CHECK consistency → OK (critical/warnings/actors ≤ total={})", total)

    logger.info("RESULT: audit-log stats verified ({} events in 24h)", resp.data["totalEvents24h"])


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_audit_log_003(sa_partners_client):
    """PARTNER_API_AUDIT_LOG_003: SA exports the audit log as JSON or CSV (within the 10k-row cap).

    Read-only contract on ``GET /sa-partners-api/v1/sa/audit-logs/export``: returns
    HTTP 200 with a downloadable file — ``format=json`` yields an
    ``application/json`` array of audit entries, ``format=csv`` yields ``text/csv``
    with an audit-column header, and no ``format`` defaults to CSV. The export is
    capped at 10000 rows.
    """
    async with async_step("[1/3] Export as JSON"):
        r = await sa_partners_client.export_audit_logs(format="json")
        assert r.status_code == 200, f"expected 200, got {r.status_code}"
        assert "application/json" in r.headers.get("content-type", "").lower(), (
            "JSON export must be application/json"
        )
        rows = r.json()
        assert isinstance(rows, list), "JSON export body must be a list"
        assert len(rows) <= 10000, f"export must respect the 10000-row cap, got {len(rows)}"
        if rows:
            for f in ("_id", "action", "category", "severity", "createdAt"):
                assert f in rows[0], f"export row must include {f}"
        logger.info("CHECK json → OK ({} rows, <=10000)", len(rows))

    async with async_step("[2/3] Export as CSV"):
        r = await sa_partners_client.export_audit_logs(format="csv")
        assert r.status_code == 200, f"expected 200, got {r.status_code}"
        assert "text/csv" in r.headers.get("content-type", "").lower(), (
            "CSV export must be text/csv"
        )
        header = r.text.splitlines()[0] if r.text else ""
        for col in ("_id", "createdAt", "category", "severity", "action"):
            assert col in header, f"CSV header must include {col}"
        logger.info("CHECK csv → OK (header carries audit columns)")

    async with async_step("[3/3] No format defaults to CSV"):
        r = await sa_partners_client.export_audit_logs()
        assert r.status_code == 200, f"expected 200, got {r.status_code}"
        assert "text/csv" in r.headers.get("content-type", "").lower(), (
            "default export should be CSV"
        )
        logger.info("CHECK default → OK (defaults to CSV)")

    logger.info("RESULT: audit-log export verified (json + csv, <=10000 rows)")


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_audit_log_006(sa_partners_client):
    """PARTNER_API_AUDIT_LOG_006: export with invalid format/filter - rejected (4xx, never 5xx).

    Negative counterpart of _003. An out-of-enum ``format`` or filter
    (severity/category/actorType/retentionClass) and a bad-format date must be
    rejected with 4xx (never 5xx) + a clear message. All cases run (failures
    collected) so one gap never hides others.
    """
    # (label, params, expected message hint)
    cases = [
        ("bogus format", {"format": "bogus"}, "format must be one of"),
        ("invalid severity", {"format": "json", "severity": "bogus"}, "severity must be one of"),
        ("invalid category", {"format": "json", "category": "bogus"}, "category must be one of"),
        ("invalid actorType", {"format": "json", "actorType": "bogus"}, "actortype must be one of"),
        (
            "invalid retentionClass",
            {"format": "json", "retentionClass": "bogus"},
            "retentionclass must be one of",
        ),
        (
            "bad dateFrom",
            {"format": "json", "dateFrom": "31-12-2026"},
            "datefrom must be a valid iso",
        ),
        ("bad dateTo", {"format": "json", "dateTo": "not-a-date"}, "dateto must be a valid iso"),
    ]
    gaps: list[str] = []
    for idx, (label, params, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject export: {label}"):
            r = await sa_partners_client.export_audit_logs(expected_status=None, **params)
            try:
                msg = str(r.json().get("message") or "")
            except ValueError:
                msg = r.text[:120]
            if 400 <= r.status_code < 500 and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code}, msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    assert not gaps, "audit-log export negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: all {} invalid export attempts rejected (4xx, never 5xx)", len(cases))


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_audit_log_004(sa_partners_client):
    """PARTNER_API_AUDIT_LOG_004: SA retrieves a single audit-log entry by id - full detail.

    Read-only contract on ``GET /sa-partners-api/v1/sa/audit-logs/{id}``: fetching a
    real entry id (taken from the list) returns HTTP 200 with the envelope and the
    FULL entry in ``data`` (id matches; action/category/severity/createdAt present;
    actor/resource objects), leaking no sensitive field.
    """
    async with async_step("[1/2] Pick a real entry id from the list"):
        listed = await sa_partners_client.list_audit_logs(limit=1)
        if not listed.data:
            pytest.skip("audit log is empty on this environment — no entry to fetch by id")
        log_id = listed.data[0].get("_id") or listed.data[0].get("id")
        assert log_id, "list entry must carry an id"
        logger.info("SETUP: fetching audit entry {}", log_id)

    async with async_step("[2/2] GET by id returns the full entry"):
        resp = await sa_partners_client.get_audit_log(log_id)
        assert resp.status_code == 200, f"expected body statusCode 200, got {resp.status_code}"
        d = resp.data
        assert isinstance(d, dict) and d, "`data` must be a non-empty object"
        assert (d.get("_id") or d.get("id")) == log_id, "GET by id must return the same entry"
        for f in ("action", "category", "severity", "createdAt"):
            assert d.get(f), f"entry must include {f}"
        assert isinstance(d.get("actor"), dict), "actor must be an object"
        assert isinstance(d.get("resource"), dict), "resource must be an object"
        leaked = [k for k in d if any(s in str(k).lower() for s in _SENSITIVE)]
        assert not leaked, f"entry must not expose sensitive keys: {leaked}"
        logger.info("CHECK by-id → OK (full entry returned, no sensitive leak)")

    logger.info("RESULT: audit entry {} retrieved by id (full detail)", log_id)


@pytest.mark.api
@pytest.mark.regression
async def test_partner_api_audit_log_007(sa_partners_client):
    """PARTNER_API_AUDIT_LOG_007: get audit entry with invalid id - rejected (4xx, never 5xx).

    Negative counterpart of _004. A non-existent (ghost) id returns 404 ('not
    found') and a malformed id returns 400 ('Invalid id') — self-proving, no real
    entry needed. All cases run (failures collected) so one gap never hides others.
    """
    # (label, id, expected status, expected message hint)
    cases = [
        ("ghost id", "000000000000000000000000", 404, "not found"),
        ("malformed id", "not-an-id", 400, "invalid id"),
    ]
    gaps: list[str] = []
    for idx, (label, log_id, expected, hint) in enumerate(cases, start=1):
        async with async_step(f"[{idx}/{len(cases)}] Reject get-by-id: {label}"):
            r = await sa_partners_client.raw_get_audit_log(log_id)
            try:
                msg = str(r.json().get("message") or "")
            except ValueError:
                msg = r.text[:120]
            if r.status_code == expected and hint.lower() in msg.lower():
                logger.info("CHECK {} → OK ({}, msg~'{}')", label, r.status_code, hint)
            else:
                gaps.append(f"{label}: status={r.status_code} (want {expected}), msg={msg!r}")
                logger.error("CHECK {} → FAIL (status={}, msg={!r})", label, r.status_code, msg)

    assert not gaps, "audit get-by-id negative gaps:\n  - " + "\n  - ".join(gaps)
    logger.info("RESULT: invalid get-by-id rejected (404 ghost / 400 malformed)")
