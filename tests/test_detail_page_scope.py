"""Regression tests for is_detail_page scope rules (GENERIC).

Covers the generic behavior with synthetic domains/URLs — no real subjects:
- profile-scope rule (single-segment slug seeds block other slugs)
- multi-segment off-subject blocking (listing trees like /models/*)
- search-query seeds + generic utility-prefix block (/s/, /o/, /user/, ...)
- generic single-segment seed without a token is not treated as a profile
- link_pattern_allows: permissive whitelist semantics (no pattern = allow all;
  anchored + substring matching on the path; configured patterns enforced)
- coordinator chain: normalize -> is_detail_page AND link_pattern_allows
"""
from __future__ import annotations

from core.managers import DomainRulesManager
from core.filters import normalize_url


def _detail(mgr: DomainRulesManager, link: str, seed: str, tokens: list[str]) -> bool:
    return mgr.is_detail_page(link, seed, "somesubject", tokens)


# ---------------------------------------------------------------------------
# Profile-scope rule: single-segment slug seed
# ---------------------------------------------------------------------------
def test_profile_scope_blocks_other_slugs():
    mgr = DomainRulesManager()
    seed = "https://example.com/somesubject"
    cases = [
        ("https://example.com/somesubject", False),          # seed itself
        ("https://example.com/somesubject/Photos", True),    # section
        ("https://example.com/somesubject/9627870", True),   # post
        ("https://example.com/somesubject/Videos", True),    # section
        ("https://example.com/othermodel", False),           # other model slug
        ("https://example.com/privacy-policy", False),       # utility (nav_paths)
        ("https://example.com/2257", False),                 # compliance (nav_paths)
        ("https://example.com/random/medias", False),        # random feed (nav_paths)
        ("https://example.com/manifest.webmanifest", False), # asset (nav_paths)
    ]
    for link, expected in cases:
        got = _detail(mgr, link, seed, ["somesubject"])
        assert got == expected, f"{link}: got {got}, expected {expected}"


# ---------------------------------------------------------------------------
# Profile-scope rule: multi-segment off-subject links (listing trees)
# ---------------------------------------------------------------------------
def test_profile_scope_blocks_multi_segment_off_subject():
    mgr = DomainRulesManager()
    seed = "https://example.com/somesubject"
    tokens = ["somesubject", "subject_alias"]
    cases = [
        ("https://example.com/somesubject", False),                       # seed itself
        ("https://example.com/somesubject/media/123", True),              # subject media
        ("https://example.com/somesubject/1/full/img_001.webp", True),    # subject asset
        ("https://example.com/models/l/a/la-chinita", False),             # OTHER model (multi-seg)
        ("https://example.com/models/v/e/vereena-sayed", False),          # OTHER model
        ("https://example.com/models/t/h/thais-geliski/1/full/thais-geliski_0068.webp", False),
        ("https://example.com/models/z/a/zarawolf-1/1/full/zarawolf-1_0011.webp", False),
    ]
    for link, expected in cases:
        got = _detail(mgr, link, seed, tokens)
        assert got == expected, f"{link}: got {got}, expected {expected}"


# ---------------------------------------------------------------------------
# Search-query seeds + generic utility-prefix block
# ---------------------------------------------------------------------------
def test_search_seed_blocks_utility_and_other_creator():
    mgr = DomainRulesManager()
    seed = "https://example.com/search?q=somesubject"
    tokens = ["somesubject", "subject_alias"]
    cases = [
        ("https://example.com/a/2LejSxv1", True),             # subject post (opaque ID ns)
        ("https://example.com/OtherCreator", False),          # other creator (single-seg slug)
        ("https://example.com/s/faq", False),                 # utility (/s/)
        ("https://example.com/s/terms", False),               # utility (/s/)
        ("https://example.com/o/menu-1", False),              # utility (/o/)
        ("https://example.com/s/report", False),              # utility (/s/)
        ("https://example.com/s/contact", False),             # utility (/s/)
        ("https://example.com/s/creators", False),            # utility (/s/)
        ("https://example.com/user/login", False),            # auth (/user/)
        ("https://example.com/login/google", False),          # auth (/login/)
        ("https://example.com/version/all", False),           # version feed (/version/)
        ("https://example.com/safari-pinned-tab.svg", False), # asset (extension)
    ]
    for link, expected in cases:
        got = _detail(mgr, link, seed, tokens)
        assert got == expected, f"{link}: got {got}, expected {expected}"


# ---------------------------------------------------------------------------
# Generic single-segment seed WITHOUT a token -> not a profile
# ---------------------------------------------------------------------------
def test_generic_seed_without_token_not_profile():
    mgr = DomainRulesManager()
    seed = "https://example.com/start"
    # seed path "start" contains no subject token -> rule never fires
    assert _detail(mgr, "https://example.com/page0", seed, ["somesubject"]) is True


# ---------------------------------------------------------------------------
# link_pattern_allows: permissive whitelist semantics
# ---------------------------------------------------------------------------
def test_link_pattern_allows_permissive_semantics(tmp_path):
    import json

    config_file = tmp_path / "domain_config.json"
    profile_file = tmp_path / "subject_profiles.json"
    profile_file.write_text("{}", encoding="utf-8")

    # Domain WITHOUT a pattern -> allow everything
    config_file.write_text(
        json.dumps({"domain_handlers": {"open.example": {}}}), encoding="utf-8"
    )
    mgr = DomainRulesManager(str(config_file), str(profile_file))
    assert mgr.link_pattern_allows("https://open.example/anything/here", "open.example") is True

    # Domain WITH an anchored path pattern -> only matching paths
    config_file.write_text(
        json.dumps(
            {
                "domain_handlers": {
                    "anchored.example": {
                        "link_pattern": r"^(/[^/]+(/[\d]+)?/?|/assets/.*)$"
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    mgr = DomainRulesManager(str(config_file), str(profile_file))
    assert mgr.link_pattern_allows("https://anchored.example/profile", "anchored.example") is True
    assert mgr.link_pattern_allows("https://anchored.example/profile/42", "anchored.example") is True
    assert mgr.link_pattern_allows("https://anchored.example/assets/img.png", "anchored.example") is True
    assert mgr.link_pattern_allows("https://anchored.example/random/feed", "anchored.example") is False

    # Substring (unanchored) pattern still works on the path
    config_file.write_text(
        json.dumps(
            {"domain_handlers": {"substr.example": {"link_pattern": r"/video/"}}}
        ),
        encoding="utf-8",
    )
    mgr = DomainRulesManager(str(config_file), str(profile_file))
    assert mgr.link_pattern_allows("https://substr.example/watch/video/123", "substr.example") is True
    assert mgr.link_pattern_allows("https://substr.example/home", "substr.example") is False


# ---------------------------------------------------------------------------
# Coordinator chain: normalize -> is_detail_page AND link_pattern_allows
# ---------------------------------------------------------------------------
def test_filter_chain(tmp_path):
    import json

    config_file = tmp_path / "domain_config.json"
    profile_file = tmp_path / "subject_profiles.json"
    profile_file.write_text("{}", encoding="utf-8")
    config_file.write_text(
        json.dumps(
            {
                "domain_handlers": {
                    "example.com": {
                        "link_pattern": r"^(/[^/]+(/[^/]+(/[^/]+)?)?/?|/assets/.*)$"
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    mgr = DomainRulesManager(str(config_file), str(profile_file))
    seed = "https://example.com/somesubject"
    host = "example.com"
    cases = [
        ("https://example.com/somesubject", True),           # seed itself (direct)
        ("https://example.com/somesubject/Photos", True),    # section
        ("https://example.com/somesubject/42", True),        # numeric post
        ("https://example.com/somesubject/42/2", True),      # paginated post
        ("https://example.com/othermodel", False),           # other model (is_detail_page)
        ("https://example.com/random/feed", False),          # random feed (pattern)
        ("https://example.com/assets/img.png", False),       # asset (is_detail_page: /assets/ nav)
        ("https://example.com/manifest.webmanifest", False), # asset (nav_paths)
    ]
    for link, expected in cases:
        norm = normalize_url(link)
        detail = mgr.is_detail_page(norm, seed, "somesubject", ["somesubject"])
        pattern = mgr.link_pattern_allows(norm, host)
        got = True if norm.rstrip("/") == seed.rstrip("/") else (detail and pattern)
        assert got == expected, f"{link}: got {got}, expected {expected}"
