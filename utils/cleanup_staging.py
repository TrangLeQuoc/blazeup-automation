"""Sweep leftover ``QA-AUTO`` partner test data off a shared environment.

Tests register a cleanup for everything they create (the ``created_resources``
fixture), so a clean run leaves nothing behind. But a killed run, a hard crash,
or a partner the BE refuses to delete because it still has deals (the deal API
has no delete endpoint, so deals are only cleaned via their parent partner) can
leak ``QA-AUTO``-tagged partners onto staging. Over time that pollutes the
environment and can skew cross-partner conflict tests.

This maintenance script finds those leftovers by their ``QA-AUTO`` name prefix
and deletes them.

Safe by default: it LISTS what it would delete and stops. Pass ``--execute`` to
actually delete. Partners the BE refuses to delete (e.g. still referenced by a
deal) are reported, not hidden.

Usage::

    # dry-run: show what would be removed, delete nothing
    python -m utils.cleanup_staging

    # actually delete the QA-AUTO partners
    python -m utils.cleanup_staging --execute

Credentials + target come from the same Settings/.env the tests use
(``BLAZEUP_DOMAIN`` selects the env file).
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from loguru import logger

from api_clients.blazeup_admin.sa_partners_client import SaPartnersClient
from config.settings import get_settings
from utils.data_factory import QA_AUTO_PREFIX
from utils.login_helpers import login_api


async def _collect_qa_partners(client: SaPartnersClient, *, page_limit: int = 100) -> list[dict]:
    """Page through all partners, keeping only the ``QA-AUTO``-tagged ones."""
    found: list[dict] = []
    page = 1
    while True:
        resp = await client.list_partners(page=page, limit=page_limit)
        batch = resp.data
        if not batch:
            break
        found.extend(p for p in batch if str(p.get("name", "")).startswith(QA_AUTO_PREFIX))
        if len(batch) < page_limit:
            break
        page += 1
    return found


async def _run(execute: bool) -> int:
    settings = get_settings()
    # Not under pytest here, so check credentials directly (require_credentials
    # would call pytest.skip, which only makes sense inside a test).
    email, password = settings.test_email, settings.test_password
    if not email or not password:
        raise SystemExit(
            "TEST_EMAIL and TEST_PASSWORD must be set in config/<domain>/.env to run the sweep."
        )
    # Generous timeout: this is a maintenance sweep, not the assertion under test,
    # and a full partner listing on staging can be slow.
    slow_limit = settings.default_response_time_ms * 5
    token = await login_api(
        str(settings.api_base_url),
        str(settings.base_url),
        email,
        password,
        max_response_time_ms=slow_limit,
    )
    client = SaPartnersClient(
        str(settings.api_base_url),
        token=token,
        max_response_time_ms=slow_limit,
        app_origin=str(settings.base_url),
    )
    try:
        partners = await _collect_qa_partners(client)
        if not partners:
            logger.info("No QA-AUTO partners found — environment is clean.")
            return 0

        logger.info("Found {} QA-AUTO partner(s):", len(partners))
        for p in partners:
            logger.info(
                "  - {} | {} | status={}",
                p.get("_id") or p.get("id"),
                p.get("name"),
                p.get("status"),
            )

        if not execute:
            logger.warning(
                "DRY-RUN: nothing deleted. Re-run with --execute to delete the {} partner(s) above.",
                len(partners),
            )
            return 0

        deleted = failed = 0
        for p in partners:
            pid = p.get("_id") or p.get("id")
            if not pid:
                continue
            try:
                await client.delete_partner(pid)
                deleted += 1
            except Exception as exc:  # noqa: BLE001 — report each failure and continue
                failed += 1
                logger.warning("Could not delete {} ({}): {}", pid, p.get("name"), exc)
        logger.info("Deleted {} partner(s); {} could not be deleted.", deleted, failed)
        return 1 if failed else 0
    finally:
        await client.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Delete leftover QA-AUTO partner test data.")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="actually delete (default is a dry-run that only lists what it would remove)",
    )
    args = parser.parse_args(argv)
    return asyncio.run(_run(args.execute))


if __name__ == "__main__":
    sys.exit(main())
