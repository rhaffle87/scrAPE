"""FastAPI router for Seed Studio manifest discovery, linting, validation, and CRUD operations."""

from __future__ import annotations

import asyncio
import logging
import os
from pathlib import Path
import random
import re
from typing import List, Optional
import urllib.parse

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from frontend.state import SEEDS_DIR, OUTPUT_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["seeds"])


class SaveSeedPayload(BaseModel):
    filename: str
    content: str
    overwrite: Optional[bool] = False


class ValidateSeedPayload(BaseModel):
    content: str


class DiscoverSeedPayload(BaseModel):
    query: str
    domains: List[str]


class SeedDiscoverRequest(BaseModel):
    subject: str


class SeedLintRequest(BaseModel):
    content: str


@router.get("/seeds")
def list_seeds():
    from src.core.seed_manifest import SeedManifest

    seeds = []
    for p in sorted(SEEDS_DIR.glob("*.txt")):
        try:
            manifest = SeedManifest.from_file(p)
            seeds.append({
                "filename": p.name,
                "subject_name": manifest.subject_name or p.stem,
                "domain_count": len(manifest.domains),
                "url_count": len(manifest.all_seed_urls),
                "domains": [d.domain for d in manifest.domains],
            })
        except Exception:
            seeds.append({
                "filename": p.name,
                "subject_name": p.stem,
                "domain_count": 0,
                "url_count": 0,
                "domains": [],
            })
    return {"seeds": seeds}


@router.get("/seeds/{filename}")
def get_seed(filename: str):
    from src.core.seed_manifest import SeedManifest

    # Sanitize: use basename to break CodeQL taint chain
    safe_filename = os.path.basename(filename)
    if not safe_filename or not re.match(r"^[\w\-. ]+$", safe_filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    seeds_base = os.path.abspath(str(SEEDS_DIR))
    target_path = os.path.abspath(os.path.join(seeds_base, safe_filename))
    if not target_path.startswith(seeds_base + os.sep):
        raise HTTPException(status_code=400, detail="Invalid path")
    target = Path(target_path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Seed file not found")
    content = target.read_text(encoding="utf-8")
    try:
        manifest = SeedManifest.from_file(target)
        profiles = []
        for d in manifest.domains:
            profiles.append({
                "domain": d.domain,
                "seed_urls": d.seed_urls,
                "media_type": d.media_type,
                "crawl_strategy": d.crawl_strategy,
                "crawl_depth": d.crawl_depth,
                "rate_limit": d.rate_limit,
                "preferred_engine": d.preferred_engine,
                "cloudflare_blocked": d.cloudflare_blocked,
                "requires_referer": d.requires_referer,
                "disabled": d.disabled,
            })
        return {
            "filename": filename,
            "content": content,
            "subject_name": manifest.subject_name,
            "domains": profiles,
        }
    except Exception:
        return {
            "filename": filename,
            "content": content,
            "subject_name": target.stem,
            "domains": [],
        }


@router.post("/seeds")
def save_seed(payload: SaveSeedPayload):
    filename = os.path.basename(payload.filename.strip())
    if not filename or not re.match(r"^[\w\-. ]+$", filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not filename.endswith(".txt"):
        filename = f"{filename}.txt"

    seeds_base = os.path.abspath(str(SEEDS_DIR))
    target_path = os.path.abspath(os.path.join(seeds_base, filename))
    if not target_path.startswith(seeds_base + os.sep):
        raise HTTPException(status_code=400, detail="Invalid path")
    target = Path(target_path)
    if target.exists() and not payload.overwrite:
        raise HTTPException(status_code=409, detail="File already exists")

    target.write_text(payload.content, encoding="utf-8")
    return {"success": True, "filename": filename, "message": "Seed file saved successfully"}


@router.delete("/seeds/{filename}")
def delete_seed(filename: str):
    safe_filename = os.path.basename(filename)
    if not safe_filename or not re.match(r"^[\w\-. ]+$", safe_filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    seeds_base = os.path.abspath(str(SEEDS_DIR))
    target_path = os.path.abspath(os.path.join(seeds_base, safe_filename))
    if not target_path.startswith(seeds_base + os.sep):
        raise HTTPException(status_code=400, detail="Invalid path")
    target = Path(target_path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Seed file not found")
    target.unlink()
    return {"success": True, "filename": safe_filename, "message": "Seed file deleted"}


@router.post("/seeds/validate")
def validate_seed(payload: ValidateSeedPayload):
    from src.core.seed_manifest import SeedManifest

    temp_file = SEEDS_DIR / "_temp_val.txt"
    try:
        temp_file.write_text(payload.content, encoding="utf-8")
        warnings = SeedManifest.validate(temp_file)
        return {"warnings": warnings, "is_valid": len(warnings) == 0}
    finally:
        if temp_file.exists():
            temp_file.unlink()


@router.post("/seeds/discover")
async def discover_search_urls(payload: DiscoverSeedPayload):
    from src.network.http_client import HttpClient

    query = payload.query.strip()
    if not query:
        return {"discovered_urls": [], "tested_count": 0, "valid_count": 0}

    encoded_q = urllib.parse.quote(query)
    candidate_urls = []

    # 1. Multi-Engine Search Probes (SafeSearch disabled kp=-2)
    search_probes = [
        f"https://html.duckduckgo.com/html/?q={encoded_q}&kp=-2",
        f"https://duckduckgo.com/html/?q={encoded_q}&kp=-2",
        f"https://www.google.com/search?q={encoded_q}&tbm=isch",
    ]
    candidate_urls.extend(search_probes)

    for dom in payload.domains:
        dom = dom.strip()
        if not dom:
            continue
        if not dom.startswith("http://") and not dom.startswith("https://"):
            base_url = f"https://{dom}"
        else:
            base_url = dom

        base_url = base_url.rstrip("/")

        candidates = [
            f"{base_url}/?f_search={encoded_q}",
            f"{base_url}/posts?tags={encoded_q}",
            f"{base_url}/tags/{encoded_q}",
            f"{base_url}/m/{encoded_q}",
            f"{base_url}/user/{encoded_q}",
            f"{base_url}/search/{encoded_q}",
            f"{base_url}/search?q={encoded_q}",
            f"{base_url}/?s={encoded_q}",
            f"{base_url}/t/{encoded_q}",
            f"{base_url}/category/{encoded_q}",
        ]
        candidate_urls.extend(candidates)

    candidate_urls = list(dict.fromkeys(candidate_urls))

    client = HttpClient(timeout=6.0)

    async def probe_url(url: str):
        await asyncio.sleep(random.uniform(0.05, 0.25))
        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, lambda: client.get(url))
            if res is not None:
                headers_lower = {k.lower(): v.lower() for k, v in res.headers.items()}
                is_cf = "cloudflare" in headers_lower.get("server", "") or "cf-ray" in headers_lower
                is_403_429 = res.status_code in (403, 429)

                status_code = res.status_code
                is_valid = status_code == 200 and len(res.content) > 300

                annotations = {
                    "cloudflare_blocked": is_cf or is_403_429,
                    "preferred_engine": "camoufox" if (is_cf or is_403_429) else "auto",
                    "requires_referer": status_code in (403, 401),
                }

                if is_valid or is_cf or is_403_429:
                    return {
                        "url": url,
                        "status": status_code,
                        "valid": is_valid,
                        "annotations": annotations,
                    }
        except Exception:
            pass
        return {"url": url, "status": 404, "valid": False, "annotations": {}}

    tasks = [probe_url(u) for u in candidate_urls]
    results = await asyncio.gather(*tasks)

    valid_urls = [r for r in results if r["valid"]]
    return {
        "discovered_urls": valid_urls,
        "tested_count": len(candidate_urls),
        "valid_count": len(valid_urls),
    }


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
