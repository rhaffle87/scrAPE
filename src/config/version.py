import re
from pathlib import Path

def get_version() -> str:
    """Read the version dynamically from pyproject.toml."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    pyproject_path = root_dir / "pyproject.toml"
    
    if not pyproject_path.exists():
        return "0.0.0-unknown"
        
    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'version\s*=\s*"([^"]+)"', content)
    if match:
        return match.group(1)
    return "0.0.0-unknown"

VERSION = get_version()
VERSION_TAG = f"v{VERSION}"
