import sys
import os
import pytest

# Add src folder to path so tests can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

@pytest.fixture
def mock_settings():
    """Returns a dictionary mocked like a SettingsManager content."""
    return {
        "shortcuts": {
            "play_pause": "<ctrl>+<shift>+<space>",
            "next_track": "<ctrl>+<shift>+<right>",
            "prev_track": "<ctrl>+<shift>+<left>"
        },
        "volume_level": 80,
        "download_dir": ""
    }
