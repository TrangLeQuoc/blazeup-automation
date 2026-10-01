"""step(..., soft=gaps): a step that adds a gap is tagged with its number and never raises."""

import asyncio

from utils.log_helper import _step_label, async_step, step


def test_label_is_the_step_number_when_present():
    assert _step_label("[2/5] The slug must resolve") == "[2/5]"
    assert _step_label("Setup: open the page") == "[Setup: open the page]"


def test_sync_step_tags_new_gaps_and_does_not_raise():
    gaps = ["[1/3] earlier gap"]
    with step("[2/3] Check X", soft=gaps):
        gaps.append("X answered 400")
    assert gaps == ["[1/3] earlier gap", "[2/3] X answered 400"]


def test_async_step_tags_new_gaps_and_does_not_raise():
    gaps: list[str] = []

    async def run():
        async with async_step("[3/3] Check Y", soft=gaps):
            gaps.append("Y crashed (500)")
        async with async_step("[3/3] Clean step", soft=gaps):
            pass

    asyncio.run(run())
    assert gaps == ["[3/3] Y crashed (500)"]


def test_a_real_exception_still_propagates():
    gaps: list[str] = []
    try:
        with step("[1/1] Boom", soft=gaps):
            raise ValueError("hard failure")
    except ValueError:
        pass
    else:
        raise AssertionError("a hard failure inside a soft step must not be swallowed")
