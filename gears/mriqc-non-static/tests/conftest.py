from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_context(mocker):
    mocker.patch("flywheel_gear_toolkit.GearToolkitContext")
    gtk_context = MagicMock(autospec=True)
    return gtk_context
