import sys
from pathlib import Path

# Add src to Python path for unit testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
import utils.blacklist

@pytest.fixture(autouse=True)
def mock_blacklist_path(tmp_path):
    original_path = utils.blacklist.BLACKLIST_PATH
    temp_blacklist = tmp_path / "blacklist.json"
    utils.blacklist.BLACKLIST_PATH = str(temp_blacklist)
    yield
    utils.blacklist.BLACKLIST_PATH = original_path

