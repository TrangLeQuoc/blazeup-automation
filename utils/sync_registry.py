import ast
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"
REGISTRY_FILE = PROJECT_ROOT / "runner" / "tc_registry.py"

TEMPLATE = '''"""Central registry mapping BlazeUp HRMS test case numbers to pytest nodes. (AUTO-GENERATED)"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class TestCase:
    """Metadata for a single automation test case."""

    tc_id: int
    type: Literal["api", "ui"]
    module: str
    title: str
    test_path: str
    test_func: str
    markers: list[str] = field(default_factory=list)
    priority: Literal["P1", "P2", "P3"] = "P2"

    @property
    def node_id(self) -> str:
        """Return the pytest node id for this test case."""
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
    """Return all test cases for a module."""

    return [tc for tc in TC_REGISTRY.values() if tc.module == module]


def list_by_type(tc_type: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if tc.type == tc_type]


def list_by_marker(marker: str) -> list[TestCase]:
    return [tc for tc in TC_REGISTRY.values() if marker in tc.markers]
'''


def extract_tc_info(file_path: Path) -> list[dict]:
    """Parse a test file and return metadata for each test_tc* function."""

    results = []
    tree = ast.parse(file_path.read_text(encoding="utf-8"))

    # Derive type (api/ui) and module name from the file path
    rel_path = file_path.relative_to(PROJECT_ROOT).as_posix()
    tc_type = "api" if "api" in rel_path else "ui"
    # e.g. test_auth_api.py -> "auth", test_login.py -> "login"
    module_match = re.search(r'test_(.*)_(?:api|ui)\.py|test_(.*)\.py', file_path.name)
    module = (module_match.group(1) or module_match.group(2)) if module_match else "unknown"

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.name.startswith("test_tc"):
            continue

        # tca01 -> id=1 (api), tc01 -> id=1001 (ui offset)
        id_match = re.search(r'tc(a)?(\d+)', node.name)
        if not id_match:
            continue

        raw_id = int(id_match.group(2))
        tc_id = raw_id if id_match.group(1) else 1000 + raw_id

        # Title from docstring first line, strip "TCxx: " prefix if present
        docstring = ast.get_docstring(node)
        title = docstring.split('\n')[0].split(': ', 1)[-1] if docstring else "No Title"

        # Collect @pytest.mark.<name> decorators
        markers = []
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Attribute) and isinstance(decorator.value, ast.Attribute):
                # handles @pytest.mark.smoke
                if decorator.value.attr == "mark":
                    markers.append(decorator.attr)

        priority = "P1" if "smoke" in markers else "P2"

        results.append({
            "id": tc_id,
            "type": tc_type,
            "module": module,
            "title": title.replace('"', "'"),
            "path": rel_path,
            "func": node.name,
            "markers": markers,
            "priority": priority,
        })
    return results


def sync() -> None:
    """Regenerate tc_registry.py from the current test suite."""

    all_tcs: list[dict] = []
    for py_file in TESTS_DIR.rglob("test_*.py"):
        all_tcs.extend(extract_tc_info(py_file))

    all_tcs.sort(key=lambda x: x["id"])

    items_str = ""
    for tc in all_tcs:
        items_str += (
            f'    {tc["id"]}: TestCase({tc["id"]}, "{tc["type"]}", "{tc["module"]}", '
            f'"{tc["title"]}", "{tc["path"]}", "{tc["func"]}", {tc["markers"]}, "{tc["priority"]}"),\n'
        )

    REGISTRY_FILE.write_text(TEMPLATE.format(items=items_str.rstrip()), encoding="utf-8")
    print(f"Successfully synced {len(all_tcs)} test cases to {REGISTRY_FILE}")


if __name__ == "__main__":
    sync()
