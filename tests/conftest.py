import pytest


@pytest.fixture
def household(db):
    from households.models import Household  # noqa: F401 — placeholder until real model

    pytest.skip("household model not yet implemented — scaffold")
