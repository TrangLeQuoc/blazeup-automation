#!/usr/bin/env python3
"""Regenerate runner/tc_registry.py from implemented test functions + Excel metadata.

How it works
------------
1. Scan tests/**/*.py for functions named:
       test_partner_{ui|api}_{section}_{NNN}
   e.g. test_partner_ui_partner_portal_shell_001
        test_partner_api_auth_access_control_002
2. For each function, compute the numeric TC ID from the function name alone.
3. Look up title & priority from Partner_Platform_Test_Plan.xlsx (optional).
   Falls back to function docstring / "P2" default if Excel is unavailable.
4. Also pick up legacy test_tc* / test_tca* functions (BlazeUp HRMS demo tests).
5. Write runner/tc_registry.py.

Only IMPLEMENTED test cases (i.e. functions that already exist in a test file)
are registered.  Unimplemented TCs produce no registry entry — just write the
function and run sync again.

File layout (both flat and section-subfolder are supported)
-----------------------------------------------------------
    tests/ui/test_partner_ui_dashboard.py          <- flat, all Dashboard TCs
    tests/ui/partner_portal_shell/
        test_partner_ui_partner_portal_shell.py    <- section file, all Shell TCs

Function naming convention
--------------------------
    test_partner_ui_partner_portal_shell_001   <- TC 1010101
    test_partner_ui_partner_portal_shell_002   <- TC 1010102
    test_partner_api_auth_access_control_001   <- TC 10101

TC ID Encoding
--------------
New-style (Partner Platform):
    {type}{module:02d}{section:02d}{seq:02d}  -- 7-char string, int drops leading zero

    Digit   Meaning         Values
    ------  --------------  -----------------------------------------------
    type    1 = UI, 0 = API
    module  01 = PARTNER    (future: 02 … 15)
    section 01-10 UI / 01-17 API   (see MODULE_SECTIONS below)
    seq     01-99           sequential within section

    Examples
    PARTNER_UI_PARTNER_PORTAL_SHELL_001  ->  1*01*01*01  ->  1010101
    PARTNER_UI_DASHBOARD_001             ->  1*01*02*01  ->  1010201
    PARTNER_API_AUTH_ACCESS_CONTROL_001  ->  0*01*01*01  ->    10101
    PARTNER_API_COMMISSIONS_PAYOUTS_001  ->  0*01*10*01  ->   101001

    UI IDs >= 1_000_000 (7 digits)
    API IDs <=   999_999 (<=6 digits, leading zero dropped naturally)
    -> No collision between UI and API.

Legacy-style (BlazeUp HRMS demo tests, preserved for backward-compat):
    test_tc01_*   -> 1001  (UI)
    test_tca01_*  ->    1  (API)

Usage
-----
    python utils/sync_registry.py           # sync registry
    python utils/sync_registry.py --table   # print ID reference table
"""

import ast
import re
import sys
from pathlib import Path

try:
    import openpyxl  # type: ignore
    _HAS_OPENPYXL = True
except ImportError:
    _HAS_OPENPYXL = False

PROJECT_ROOT  = Path(__file__).resolve().parent.parent
EXCEL_FILE    = PROJECT_ROOT / "Partner_Platform_Test_Plan.xlsx"
TESTS_DIR     = PROJECT_ROOT / "tests"
REGISTRY_FILE = PROJECT_ROOT / "runner" / "tc_registry.py"

# ---------------------------------------------------------------------------
# Excel sheet -> module name mapping
# Add a new entry here when a new product module gets its own Excel sheet.
# The sheet name must match exactly (case-sensitive).
# ---------------------------------------------------------------------------
EXCEL_SHEETS: dict[str, str] = {
    "Partner Platform": "PARTNER",
    # "Health System":  "HEALTH",   # ← uncomment when sheet is added
}

# ---------------------------------------------------------------------------
# Module numbers
# Add new modules here when onboarding a new product area.
# ---------------------------------------------------------------------------
MODULES: dict[str, int] = {
    "PARTNER": 1,
    # "BILLING": 2,
    # "HRMS":    3,
}

# ---------------------------------------------------------------------------
# Section / Feature numbers per module
# Keys are the sanitised part of the TC string ID (between TYPE and SEQ).
#   PARTNER_UI_MY_PIPELINE_001          -> key = "MY_PIPELINE"
#   PARTNER_API_AUTH_ACCESS_CONTROL_001 -> key = "AUTH_ACCESS_CONTROL"
# ---------------------------------------------------------------------------
MODULE_SECTIONS: dict[str, dict[str, dict[str, int]]] = {
    "PARTNER": {
        "UI": {
            "PARTNER_PORTAL_SHELL":            1,   # 01
            "DASHBOARD":                       2,   # 02
            "MY_PIPELINE":                     3,   # 03
            "MY_CLIENTS":                      4,   # 04
            "COMMISSIONS":                     5,   # 05
            "PARTNER_TEAM":                    6,   # 06
            "RESOURCES":                       7,   # 07
            "TRAINING":                        8,   # 08
            "SA_PARTNER_MODULE":               9,   # 09
            "SECURITY_COMPLIANCE":            10,   # 10
        },
        "API": {
            "AUTH_ACCESS_CONTROL":             1,   # 01
            "DASHBOARD_DATA":                  2,   # 02
            "DEAL_REGISTRATION":               3,   # 03
            "DEAL_REGISTRATION_PIPELINE":      4,   # 04
            "DEAL_APPROVAL_QUEUE":             5,   # 05
            "DEAL_COLLABORATION":              6,   # 06
            "PIPELINE_MANAGEMENT":             7,   # 07
            "TENANT_PROVISIONING_ATTRIBUTION": 8,   # 08
            "CLIENT_HEALTH_MSP":               9,   # 09
            "COMMISSIONS_PAYOUTS":            10,   # 10
            "REFERRAL_ATTRIBUTION":           11,   # 11
            "TEAM_REFERRAL_LINKS":            12,   # 12
            "PARTNER_ACCOUNT_MANAGEMENT":     13,   # 13
            "RESOURCES_SANDBOX":              14,   # 14
            "CRM_INTEGRATION":               15,   # 15
            "EVENT_ARCHITECTURE":            16,   # 16
            "SECURITY_COMPLIANCE":           17,   # 17
        },
    },
}

# ---------------------------------------------------------------------------
# Registry file template
# ---------------------------------------------------------------------------
_TEMPLATE = '''\
"""Central registry mapping numeric TC IDs to pytest nodes.  (AUTO-GENERATED — do not edit)

TC ID Encoding
--------------
New-style  :  {{type}}{{module:02d}}{{section:02d}}{{seq:02d}}
              type 1=UI / 0=API   module 01=PARTNER   section/feature 01-17
              UI IDs >= 1_000_000 * API IDs <= 999_999 -> no collision.

Legacy     :  1001-1999 = UI demo   1-99 = API demo   (BlazeUp HRMS test suite)

Traceability
------------
tc_string  links each registry entry back to the TestcaseId column in
Partner_Platform_Test_Plan.xlsx.  Empty string for legacy (HRMS) tests.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class TestCase:
    """Metadata for a single automation test case."""

    tc_id:     int
    tc_string: str                        # Excel TestcaseId  e.g. PARTNER_UI_DASHBOARD_001
    type:      Literal["api", "ui"]
    module:    str
    title:     str
    test_path: str
    test_func: str
    markers:   list[str] = field(default_factory=list)
    priority:  Literal["P1", "P2", "P3"] = "P2"

    @property
    def node_id(self) -> str:
        return f"{{self.test_path}}::{{self.test_func}}"


TC_REGISTRY: dict[int, TestCase] = {{
{items}
}}


def get_tc(tc_id: int) -> TestCase:
    if tc_id not in TC_REGISTRY:
        raise KeyError(f"TC {{tc_id}} does not exist in the registry")
    return TC_REGISTRY[tc_id]


def validate_registry() -> None:
    """Verify that all registered test functions exist (optional utility)."""
    for tc in TC_REGISTRY.values():
        path = Path(tc.test_path)
        if not path.exists():
            print(f"Warning: Test file {{tc.test_path}} missing for TC {{tc.tc_id}}")


def list_by_module(module: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if tc.module == module]


def list_by_type(tc_type: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if tc.type == tc_type]


def list_by_marker(marker: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if marker in tc.markers]
'''


# ---------------------------------------------------------------------------
# ID computation
# ---------------------------------------------------------------------------

def tc_id_from_string(tc_string_id: str) -> int:
    """Convert a TC string ID to its numeric equivalent.

    PARTNER_UI_DASHBOARD_001            -> 1010201
    PARTNER_API_AUTH_ACCESS_CONTROL_001 -> 10101

    Returns 0 on failure (unknown module / section, bad seq).
    """
    parts = tc_string_id.strip().split("_")
    # Minimum structure: MODULE_TYPE_SECTION_SEQ -> 4 parts
    if len(parts) < 4:
        return 0

    module_name = parts[0]               # PARTNER
    tc_type     = parts[1]               # UI | API
    seq_str     = parts[-1]              # 001
    section_key = "_".join(parts[2:-1])  # DASHBOARD | AUTH_ACCESS_CONTROL | ...

    try:
        seq = int(seq_str)
    except ValueError:
        return 0
    if seq < 1 or seq > 99:
        return 0

    module_num  = MODULES.get(module_name, 0)
    sections    = MODULE_SECTIONS.get(module_name, {}).get(tc_type, {})
    section_num = sections.get(section_key, 0)

    if module_num == 0 or section_num == 0:
        return 0

    type_digit = 1 if tc_type == "UI" else 0
    return int(f"{type_digit}{module_num:02d}{section_num:02d}{seq:02d}")


def tc_string_from_id(tc_id: int) -> str:
    """Reverse-decode a numeric TC ID back to a human-readable label (debug only)."""
    s            = f"{tc_id:07d}"
    type_char    = s[0]
    module_num   = int(s[1:3])
    section_num  = int(s[3:5])
    seq          = int(s[5:7])
    tc_type      = "UI" if type_char == "1" else "API"
    module_name  = next((k for k, v in MODULES.items() if v == module_num), f"MOD{module_num:02d}")
    sections     = MODULE_SECTIONS.get(module_name, {}).get(tc_type, {})
    section_name = next((k for k, v in sections.items() if v == section_num), f"SEC{section_num:02d}")
    return f"{module_name}_{tc_type}_{section_name}_{seq:02d}"


# ---------------------------------------------------------------------------
# Helper: function name -> TC string
# ---------------------------------------------------------------------------

def _func_name_to_tc_string(func_name: str) -> str | None:
    """Convert a test function name to its TC string ID.

    test_partner_ui_partner_portal_shell_001 -> PARTNER_UI_PARTNER_PORTAL_SHELL_001

    Returns None if the name doesn't match the expected pattern
    (must start with test_, end with _NNN where NNN is exactly 3 digits).
    """
    if not func_name.startswith("test_"):
        return None
    body = func_name[5:]  # strip "test_"
    parts = body.split("_")
    # Must end with a 3-digit sequence number
    if len(parts) < 4 or not re.match(r"^\d{3}$", parts[-1]):
        return None
    # First part must be a registered module (e.g. "partner")
    # This prevents legacy functions like test_tca02_..._401 from matching.
    if parts[0].upper() not in MODULES:
        return None
    return body.upper()  # PARTNER_UI_PARTNER_PORTAL_SHELL_001


def _extract_markers(node: ast.FunctionDef | ast.AsyncFunctionDef) -> list[str]:
    """Extract @pytest.mark.X decorator names from an AST function node."""
    markers = []
    for dec in node.decorator_list:
        if (
            isinstance(dec, ast.Attribute)
            and isinstance(dec.value, ast.Attribute)
            and dec.value.attr == "mark"
        ):
            markers.append(dec.attr)
    return markers


# ---------------------------------------------------------------------------
# Excel metadata source (lookup only — not the driver of what gets registered)
# ---------------------------------------------------------------------------

def build_excel_lookup() -> dict[str, dict]:
    """Build a title/priority lookup table from all module sheets in the Excel test plan.

    Reads every sheet listed in EXCEL_SHEETS. Returns:
        { "PARTNER_UI_DASHBOARD_001": {"title": "...", "priority": "P1"}, ... }

    Returns an empty dict if Excel is unavailable — sync still works using
    function docstrings and P2 defaults.
    """
    if not _HAS_OPENPYXL:
        print("[WARN] openpyxl not installed — Excel metadata unavailable. "
              "Install with: pip install openpyxl")
        return {}
    if not EXCEL_FILE.exists():
        print(f"[WARN] Excel not found: {EXCEL_FILE} — titles from docstrings, priority P2 default")
        return {}

    # Column indices (0-based in values_only rows) — same layout assumed for all sheets
    C_TC_STRING = 2   # C -> TestcaseId   (PARTNER_UI_DASHBOARD_001)
    C_TITLE     = 3   # D -> Testcase name
    C_PRIORITY  = 5   # F -> Priority

    wb     = openpyxl.load_workbook(EXCEL_FILE, data_only=True)
    lookup: dict[str, dict] = {}

    for sheet_name, module_name in EXCEL_SHEETS.items():
        if sheet_name not in wb.sheetnames:
            print(f"[WARN] Sheet '{sheet_name}' not found in Excel — skipping {module_name}")
            continue

        ws      = wb[sheet_name]
        before  = len(lookup)

        for row in ws.iter_rows(min_row=13, values_only=True):
            tc_string = row[C_TC_STRING]
            if not tc_string or not str(tc_string).startswith(f"{module_name}_"):
                continue
            tc_string = str(tc_string).strip()
            title    = str(row[C_TITLE]    or "No Title").strip().replace('"', "'")
            priority = str(row[C_PRIORITY] or "P2").strip()
            lookup[tc_string] = {"title": title, "priority": priority}

        count = len(lookup) - before
        print(f"[Excel] {count:4d} TC definitions loaded from sheet '{sheet_name}' ({module_name})")

    return lookup


# ---------------------------------------------------------------------------
# Partner Platform test scanner (new-style naming)
# ---------------------------------------------------------------------------

def scan_implemented_tcs(excel_lookup: dict[str, dict]) -> list[dict]:
    """Scan test files for implemented Partner Platform test functions.

    Discovers functions named:
        test_partner_{ui|api}_{section}_{NNN}

    A single file may contain many TC functions — all are registered.
    Title/priority come from Excel; docstring and P2 are fallbacks.
    """
    results: list[dict] = []
    seen_ids: set[int] = set()

    for py_file in sorted(TESTS_DIR.rglob("test_*.py")):
        rel_path = py_file.relative_to(PROJECT_ROOT).as_posix()

        try:
            source = py_file.read_text(encoding="utf-8")
            tree   = ast.parse(source)
        except (OSError, SyntaxError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            tc_string = _func_name_to_tc_string(node.name)
            if tc_string is None:
                continue  # not a Partner Platform TC function

            tc_id = tc_id_from_string(tc_string)
            if tc_id == 0:
                # Function name matches pattern but section/module not registered
                print(f"  [WARN] Unknown section in {py_file.name}: {node.name} "
                      f"(TC string: {tc_string})")
                continue

            if tc_id in seen_ids:
                print(f"  [ERROR] Duplicate TC ID {tc_id} ({tc_string}) "
                      f"in {rel_path} — already registered from another file")
                continue
            seen_ids.add(tc_id)

            parts   = tc_string.split("_")
            tc_type = parts[1].lower()  # ui / api
            module  = parts[0].lower()  # partner

            # Metadata: Excel first, then docstring, then defaults
            meta     = excel_lookup.get(tc_string, {})
            doc_line = (ast.get_docstring(node) or "").split("\n")[0]
            # Strip "TC_STRING: " prefix from docstring if present
            if ": " in doc_line:
                doc_line = doc_line.split(": ", 1)[-1]

            title    = meta.get("title") or doc_line or "No Title"
            priority = meta.get("priority", "P2")
            markers  = _extract_markers(node)

            results.append({
                "id":        tc_id,
                "type":      tc_type,
                "module":    module,
                "title":     title.replace('"', "'"),
                "priority":  priority,
                "path":      rel_path,
                "func":      node.name,
                "markers":   markers,
                "source":    "scan",
                "tc_string": tc_string,
            })

    return results


# ---------------------------------------------------------------------------
# Legacy BlazeUp HRMS scanner (old test_tc* / test_tca* naming)
# ---------------------------------------------------------------------------

def scan_legacy_tcs() -> list[dict]:
    """Scan test files for old-style test_tc* / test_tca* functions.

    These are BlazeUp HRMS demo tests.

    IDs are assigned sequentially (1, 2, 3, …) sorted by:
        1. type  — api before ui
        2. file  — alphabetical within each type
        3. line  — function order within each file

    tc_string is set to "demo" to distinguish them from Partner Platform TCs.
    """
    raw: list[dict] = []

    for py_file in sorted(TESTS_DIR.rglob("test_*.py")):
        rel_path = py_file.relative_to(PROJECT_ROOT).as_posix()
        tc_type  = "api" if "/api/" in rel_path else "ui"

        mod_match   = re.search(r"test_(.*)_(?:api|ui)\.py$|test_(.*)\.py$", py_file.name)
        module_name = (mod_match.group(1) or mod_match.group(2)) if mod_match else "unknown"

        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue

        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_tc"):
                continue
            if not re.search(r"test_tc(a?)\d+", node.name):
                continue

            docstring = ast.get_docstring(node) or ""
            title     = docstring.split("\n")[0].split(": ", 1)[-1] if docstring else "No Title"
            markers   = _extract_markers(node)
            priority  = "P1" if "smoke" in markers else "P2"

            raw.append({
                "type":     tc_type,
                "module":   module_name,
                "title":    title.replace('"', "'"),
                "priority": priority,
                "path":     rel_path,
                "func":     node.name,
                "markers":  markers,
                "source":   "legacy",
                "tc_string": "demo",
                "_lineno":  node.lineno,
            })

    # Sort: api first, then ui; within each group by file path then line number
    raw.sort(key=lambda x: (0 if x["type"] == "api" else 1, x["path"], x["_lineno"]))

    # Assign sequential IDs starting from 1
    results = []
    for seq, tc in enumerate(raw, start=1):
        entry = {k: v for k, v in tc.items() if k != "_lineno"}
        entry["id"] = seq
        results.append(entry)

    return results


# ---------------------------------------------------------------------------
# Main sync
# ---------------------------------------------------------------------------

def sync() -> None:
    """Regenerate runner/tc_registry.py."""

    print("Syncing TC registry ...")
    print(f"  Excel : {EXCEL_FILE}")
    print(f"  Tests : {TESTS_DIR}")
    print()

    # Step 1: Build Excel metadata lookup (title/priority only, not the driver)
    excel_lookup = build_excel_lookup()

    # Step 2: Scan implemented Partner Platform TCs from test files
    partner_tcs = scan_implemented_tcs(excel_lookup)
    partner_ids = {tc["id"] for tc in partner_tcs}
    print(f"[Scan]  {len(partner_tcs)} implemented Partner Platform TCs found")

    # Step 3: Scan legacy TCs, skip any IDs already covered by partner scan
    legacy_tcs = [tc for tc in scan_legacy_tcs() if tc["id"] not in partner_ids]
    print(f"[Legacy] {len(legacy_tcs)} BlazeUp HRMS demo TCs loaded")

    # Step 4: Merge and sort by TC ID
    all_tcs = partner_tcs + legacy_tcs
    all_tcs.sort(key=lambda x: x["id"])

    # Step 5: Check for ID collisions across sources
    seen: dict[int, str] = {}
    for tc in all_tcs:
        if tc["id"] in seen:
            print(f"  [ERROR] Duplicate TC ID {tc['id']}: "
                  f"{seen[tc['id']]} vs {tc['func']}")
        else:
            seen[tc["id"]] = tc["func"]

    # Step 6: Render and write registry file
    items_lines = []
    for tc in all_tcs:
        tc_string = tc.get("tc_string", "")   # "" for legacy tests
        items_lines.append(
            f'    {tc["id"]}: TestCase('
            f'{tc["id"]}, '
            f'"{tc_string}", '
            f'"{tc["type"]}", '
            f'"{tc["module"]}", '
            f'"{tc["title"]}", '
            f'"{tc["path"]}", '
            f'"{tc["func"]}", '
            f'{tc["markers"]}, '
            f'"{tc["priority"]}"),'
        )

    REGISTRY_FILE.write_text(
        _TEMPLATE.format(items="\n".join(items_lines)),
        encoding="utf-8",
    )

    # Step 7: Print summary
    n_partner = sum(1 for tc in all_tcs if tc["source"] == "scan")
    n_legacy  = sum(1 for tc in all_tcs if tc["source"] == "legacy")

    print()
    print(f"  Total   : {len(all_tcs):4d}  TCs written to {REGISTRY_FILE.relative_to(PROJECT_ROOT)}")
    print(f"  Partner : {n_partner:4d}  (implemented Partner Platform tests)")
    print(f"  Legacy  : {n_legacy:4d}  (BlazeUp HRMS demo tests)")
    print()
    if n_partner == 0:
        print("  Tip: Create test functions named test_partner_ui_<section>_NNN")
        print("       or test_partner_api_<feature>_NNN and re-run sync.")
    else:
        print("  Tip: Add more test_partner_* functions to any test file and")
        print("       re-run sync — they will be auto-registered.")


# ---------------------------------------------------------------------------
# Reference table printer
# ---------------------------------------------------------------------------

def print_id_table() -> None:
    """Print the full section -> numeric-prefix table for reference."""
    print("TC ID Reference Table")
    print("=" * 65)
    for mod_name, mod_num in MODULES.items():
        print(f"\n  Module: {mod_name} ({mod_num:02d})")
        for tc_type, sections in MODULE_SECTIONS.get(mod_name, {}).items():
            type_digit = 1 if tc_type == "UI" else 0
            print(f"    {tc_type}:")
            for sec_name, sec_num in sections.items():
                first_id = int(f"{type_digit}{mod_num:02d}{sec_num:02d}01")
                print(f"      {sec_num:02d}  {sec_name:<42s}  first ID: {first_id}")


if __name__ == "__main__":
    if "--table" in sys.argv:
        print_id_table()
    else:
        sync()
