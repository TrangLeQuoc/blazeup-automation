"""The four heuristics that judge whether the backend's unit tests protect anything.

Each one drives a conversation with BE, so a false positive is expensive: report a test
that is doing its job and the whole report gets dismissed. Every case below was checked by
hand against the real repo on 2026-08-12 before being pinned here.

The detectors read source text, so these fixtures are hand-written TypeScript on a tmp
tree — no backend clone, no network.
"""

import pytest

from utils.be_unit_audit import (
    check_circular_tests,
    check_guards_untested,
    check_happy_path_only,
    check_not_found_is_400,
)


@pytest.fixture
def src(tmp_path):
    """Build a fake src/ tree from {relative path: contents}."""

    def _build(files: dict[str, str]):
        root = tmp_path / "src"
        for name, body in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        return root

    return _build


# ── A. not-found answered with 400 ──────────────────────────────────────────
# Two shapes. The second dominates in the real repo (29 sites vs 3), and a detector that
# only reads the literal throw misses almost the whole family.


def test_literal_bad_request_for_not_found_is_flagged(src):
    root = src({"a.service.ts": "throw new BadRequestException(`Partner ${id} not found`)"})
    found = check_not_found_is_400(root)
    assert len(found) == 1
    assert "not found" in found[0].what


def test_is_throw_helper_with_a_not_found_message_is_flagged(src):
    """The shared Method helper raises BadRequestException — same 400, no literal throw."""
    root = src(
        {
            "a.service.ts": """
    return this.partnerMethod.findById(id, {
      isThrow: true,
      message: `Partner ${id} not found`,
      lean: true,
    })
"""
        }
    )
    found = check_not_found_is_400(root)
    assert len(found) == 1
    assert "isThrow" in found[0].what


def test_a_bad_request_that_is_not_about_absence_is_left_alone(src):
    """400 is the RIGHT answer for a malformed request — only absence is the finding."""
    root = src({"a.service.ts": "throw new BadRequestException('reason must not be empty')"})
    assert check_not_found_is_400(root) == []


def test_is_throw_without_a_not_found_message_is_left_alone(src):
    root = src({"a.service.ts": "findById(id, { isThrow: true, message: 'invalid id' })"})
    assert check_not_found_is_400(root) == []


def test_a_correct_not_found_exception_is_left_alone(src):
    root = src({"a.service.ts": "if (!deal) throw new NotFoundException(`Deal ${id} not found`)"})
    assert check_not_found_is_400(root) == []


def test_specs_are_not_scanned_for_this_check(src):
    """A spec asserting the current behaviour is check B's business, not check A's."""
    root = src({"a.service.spec.ts": "new BadRequestException('not found')"})
    assert check_not_found_is_400(root) == []


# ── B. name claims a rule, body only proves propagation ─────────────────────


def test_mock_then_assert_the_same_exception_is_flagged(src):
    root = src(
        {
            "a.spec.ts": """
    it('throws when not found', async () => {
      method.findById.mockRejectedValue(new BadRequestException('not found'))
      await expect(service.findById('x')).rejects.toThrow(BadRequestException)
    })
"""
        }
    )
    found = check_circular_tests(root)
    assert len(found) == 1
    assert "throws when not found" in found[0].what


def test_a_test_named_for_propagation_is_exempt(src):
    """'should propagate X' promises exactly what the body proves — not a finding.

    Without this exemption `sa-audit-log.controller.spec.ts` was reported, and a report
    that flags a test doing its stated job gets dismissed wholesale.
    """
    root = src(
        {
            "a.spec.ts": """
    it('should propagate NotFoundException from service', async () => {
      service.findById.mockRejectedValue(new NotFoundException())
      await expect(controller.findById('missing')).rejects.toThrow(NotFoundException)
    })
"""
        }
    )
    assert check_circular_tests(root) == []


@pytest.mark.parametrize("word", ["delegates", "forwards", "bubbles up", "passes through"])
def test_other_propagation_wordings_are_exempt_too(src, word):
    root = src(
        {
            "a.spec.ts": f"""
    it('{word} the service error', async () => {{
      dep.go.mockRejectedValue(new BadRequestException('x'))
      await expect(svc.go()).rejects.toThrow(BadRequestException)
    }})
"""
        }
    )
    assert check_circular_tests(root) == []


def test_mocking_one_exception_and_asserting_another_is_not_circular(src):
    """The service translated the error — that is real behaviour, and worth having."""
    root = src(
        {
            "a.spec.ts": """
    it('maps a missing plan to NotFound', async () => {
      lookup.getPlan.mockRejectedValue(new BadRequestException('nope'))
      await expect(service.register({})).rejects.toThrow(NotFoundException)
    })
"""
        }
    )
    assert check_circular_tests(root) == []


def test_each_it_block_is_judged_on_its_own(src):
    """A mock in one test must not make the NEXT test look circular."""
    root = src(
        {
            "a.spec.ts": """
    it('rejects a duplicate', async () => {
      method.exists.mockRejectedValue(new BadRequestException('exists'))
      await expect(service.create({})).rejects.toThrow(BadRequestException)
    })

    it('returns the record', async () => {
      method.findById.mockResolvedValue({})
      expect(await service.findById('1')).toBeTruthy()
    })
"""
        }
    )
    found = check_circular_tests(root)
    assert len(found) == 1 and "rejects a duplicate" in found[0].what


# ── C. controller spec with no error assertion ──────────────────────────────


def test_a_controller_spec_with_only_happy_paths_is_flagged(src):
    root = src(
        {
            "a.controller.spec.ts": """
    it('delegates login', () => { expect(service.login).toHaveBeenCalled() })
    it('delegates refresh', () => { expect(service.refresh).toHaveBeenCalled() })
"""
        }
    )
    found = check_happy_path_only(root)
    assert len(found) == 1
    assert "2 test(s), 0 error assertions" in found[0].what


@pytest.mark.parametrize(
    "assertion",
    [
        "await expect(p).rejects.toThrow(Error)",
        "expect(() => f()).toThrow()",
        "expect(res.status).toBe(404)",
        "expect(res.status).toBe(500)",
        "throw new UnauthorizedException()",
    ],
)
def test_any_failure_assertion_clears_the_spec(src, assertion):
    root = src({"a.controller.spec.ts": f"it('x', () => {{ {assertion} }})"})
    assert check_happy_path_only(root) == []


def test_an_empty_spec_is_not_reported(src):
    """Nothing to say about a file with no tests — that is check C's blind spot, not a find."""
    root = src({"a.controller.spec.ts": "// TODO: write tests"})
    assert check_happy_path_only(root) == []


def test_service_specs_are_out_of_scope(src):
    """Check C is about the HTTP boundary; service error handling is tested elsewhere."""
    root = src({"a.service.spec.ts": "it('does a thing', () => { expect(1).toBe(1) })"})
    assert check_happy_path_only(root) == []


# ── D. guard declared but never exercised ───────────────────────────────────


def test_a_guard_no_spec_mentions_is_flagged(src):
    root = src(
        {
            "a.controller.ts": """
@UseGuards(PartnerJwtGuard)
export class PartnerClientsController {}
""",
            "a.controller.spec.ts": """
describe('PartnerClientsController', () => {
  it('lists clients', () => {})
})
""",
        }
    )
    found = check_guards_untested(root)
    assert len(found) == 1
    assert "PartnerJwtGuard" in found[0].what


def test_a_guard_the_spec_exercises_is_left_alone(src):
    root = src(
        {
            "a.controller.ts": """
@UseGuards(PartnerJwtGuard)
export class PartnerClientsController {}
""",
            "a.controller.spec.ts": """
describe('PartnerClientsController', () => {
  it('refuses without a token', () => { expect(PartnerJwtGuard).toBeDefined() })
})
""",
        }
    )
    assert check_guards_untested(root) == []


def test_several_guards_report_only_the_untested_ones(src):
    root = src(
        {
            "a.controller.ts": """
@UseGuards(PartnerJwtGuard, PartnerAdminGuard)
export class C {}
""",
            "a.controller.spec.ts": "describe('C', () => { it('x', () => { PartnerJwtGuard }) })",
        }
    )
    found = check_guards_untested(root)
    assert len(found) == 1
    assert "PartnerAdminGuard" in found[0].what
    assert "PartnerJwtGuard" not in found[0].what


def test_a_controller_with_no_guard_is_not_reported(src):
    root = src({"a.controller.ts": "export class C {}"})
    assert check_guards_untested(root) == []
