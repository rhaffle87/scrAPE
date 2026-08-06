"""FastAPI router for Seed Studio manifest discovery, linting, and subject listings."""

from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(prefix="/api", tags=["seeds"])

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = ROOT_DIR / "output"


class SeedDiscoverRequest(BaseModel):
    subject: str


class SeedLintRequest(BaseModel):
    content: str


@router.post("/seed/discover")
def discover_seed_manifest(req: SeedDiscoverRequest):
    """Auto-discover seed URLs for a given subject."""
    from src.cli.seed_studio import SeedDiscoverer

    discoverer = SeedDiscoverer()
    manifest_text = discoverer.discover_seeds_for_subject(req.subject)
    return {"subject": req.subject, "manifest": manifest_text}


@router.post("/seed/lint")
def lint_seed_manifest(req: SeedLintRequest):
    """Lint seed manifest text for syntax errors or deprecated annotations."""
    from src.cli.seed_studio import SeedLinter

    linter = SeedLinter()
    report = linter.lint_manifest_text(req.content)
    return report


@router.get("/subjects")
def get_subjects():
    """List all available crawled subjects in OUTPUT_DIR."""
    subjects = []
    if OUTPUT_DIR.exists():
        for path in OUTPUT_DIR.iterdir():
            if path.is_dir() and (path / "runs").exists():
                subjects.append(path.name)
    return sorted(subjects)
