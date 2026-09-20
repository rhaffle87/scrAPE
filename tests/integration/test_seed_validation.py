import pytest
from pathlib import Path
from core.seed_manifest import SeedManifest


def test_validation_on_clean_seed(tmp_path):
    seed_file = tmp_path / "clean_seed.txt"
    content = """# Subject: Orange / Test
# ----------------------------
# openverse.org
# ----------------------------
# type: mixed
# crawl: direct
# Rate-limit: 1.0 req/s
https://openverse.org/search?q=orange
"""
    seed_file.write_text(content, encoding="utf-8")
    warnings = SeedManifest.validate(seed_file)
    assert not warnings


def test_validation_missing_subject(tmp_path):
    seed_file = tmp_path / "missing_subject.txt"
    content = """# ----------------------------
# openverse.org
# ----------------------------
# type: mixed
https://openverse.org/search?q=orange
"""
    seed_file.write_text(content, encoding="utf-8")
    warnings = SeedManifest.validate(seed_file)
    assert len(warnings) == 1
    assert "Missing '# Subject: <Name>' header" in warnings[0]


def test_validation_typo_annotations(tmp_path):
    seed_file = tmp_path / "typo_seed.txt"
    content = """# Subject: Orange / Test
# ----------------------------
# openverse.org
# ----------------------------
# typ: image
# dept: 2
# ratelimit: 0.5 req/s
https://openverse.org/search?q=orange
"""
    seed_file.write_text(content, encoding="utf-8")
    warnings = SeedManifest.validate(seed_file)
    assert len(warnings) == 3
    assert any("typo in 'type'" in w for w in warnings)
    assert any("typo in 'depth'" in w for w in warnings)
    assert any("typo in 'Rate-limit'" in w for w in warnings)


def test_validation_invalid_values(tmp_path):
    seed_file = tmp_path / "invalid_vals.txt"
    content = """# Subject: Orange / Test
# ----------------------------
# openverse.org
# ----------------------------
# type: invalid_type
# crawl: invalid_crawl
# depth: abc
https://openverse.org/search?q=orange
"""
    seed_file.write_text(content, encoding="utf-8")
    warnings = SeedManifest.validate(seed_file)
    assert len(warnings) == 3
    assert any("Invalid type 'invalid_type'" in w for w in warnings)
    assert any("Invalid crawl strategy 'invalid_crawl'" in w for w in warnings)
    assert any("Invalid depth 'abc'" in w for w in warnings)


def test_validation_duplicate_urls(tmp_path):
    seed_file = tmp_path / "dupe_urls.txt"
    content = """# Subject: Orange / Test
# ----------------------------
# openverse.org
# ----------------------------
https://openverse.org/search?q=orange
https://openverse.org/search?q=orange
"""
    seed_file.write_text(content, encoding="utf-8")
    warnings = SeedManifest.validate(seed_file)
    assert len(warnings) == 1
    assert "Duplicate URL" in warnings[0]


def test_validation_malformed_lines(tmp_path):
    seed_file = tmp_path / "malformed.txt"
    content = """# Subject: Orange / Test
# ----------------------------
# openverse.org
# ----------------------------
this is a completely invalid line
"""
    seed_file.write_text(content, encoding="utf-8")
    warnings = SeedManifest.validate(seed_file)
    assert any("Invalid line format" in w for w in warnings)


def test_validation_malformed_annotations(tmp_path):
    seed_file = tmp_path / "malformed_ann.txt"
    content = """# Subject: Orange / Test
# ----------------------------
# openverse.org
# ----------------------------
# Rate-limit: 1.0
# max_pages: abc
# min-image-size: 400
# thumbnail-prefix:
https://openverse.org/search?q=orange
"""
    seed_file.write_text(content, encoding="utf-8")
    warnings = SeedManifest.validate(seed_file)
    assert len(warnings) == 4
    assert any("Malformed Rate-limit" in w for w in warnings)
    assert any("Malformed max_pages" in w for w in warnings)
    assert any("Malformed min-image-size" in w for w in warnings)
    assert any("Malformed thumbnail-prefix" in w for w in warnings)


def test_validation_empty_seed(tmp_path):
    seed_file = tmp_path / "empty.txt"
    seed_file.write_text("", encoding="utf-8")
    warnings = SeedManifest.validate(seed_file)
    assert len(warnings) == 1
    assert "Seed file is empty" in warnings[0]
