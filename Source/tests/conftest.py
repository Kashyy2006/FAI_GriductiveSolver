"""Public-only board fixtures independent of the loader and engine."""

import pytest

from game.models import PublicCharacter, PublicState, StateToken


@pytest.fixture
def public_state(request: pytest.FixtureRequest) -> PublicState:
    size = getattr(request, "param", 3)
    return PublicState(
        "public-test",
        size,
        StateToken("test-session", 0),
        tuple(
            PublicCharacter(f"{chr(65 + col)}{row + 1}", "Name", "Job", row, col)
            for row in range(size)
            for col in range(size)
        ),
    )
