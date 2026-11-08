import re

from app.db.ids import (
    FIRST_GENERATED_NUMBER,
    MA_DON,
    VE_ID,
    format_id,
    next_id,
)

ID_PATTERN = re.compile(r"^[A-Z]{2}\d{8}$")


def test_format_id_has_two_letters_and_eight_digits():
    assert format_id(VE_ID, 1) == "VE00000001"


async def test_next_id_starts_above_seed_range(session_factory):
    async with session_factory() as session:
        assert await next_id(session, VE_ID) == format_id(VE_ID, FIRST_GENERATED_NUMBER)


async def test_next_id_never_repeats_across_sessions(session_factory):
    async with session_factory() as first, session_factory() as second:
        generated = [
            await next_id(first, VE_ID),
            await next_id(second, VE_ID),
            await next_id(first, VE_ID),
        ]

    assert len(set(generated)) == 3
    assert all(ID_PATTERN.fullmatch(value) for value in generated)


async def test_each_series_counts_independently(session_factory):
    async with session_factory() as session:
        await next_id(session, VE_ID)

        assert await next_id(session, MA_DON) == format_id(MA_DON, FIRST_GENERATED_NUMBER)
