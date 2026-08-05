"""Regression: is_detail_page scope filtering applies at ALL depths, not just the
index page (depth 0). Off-model/utility links discovered on POST pages must be
blocked. Uses the public DomainRulesManager with synthetic data."""
from __future__ import annotations

from core.filters import normalize_url
from core.managers import DomainRulesManager


def test_off_model_link_blocked_at_depth1():
    """A link to another model's profile (single-seg slug) must be rejected even
    when it is discovered from a deeper page (depth >= 1), not just the index."""
    mgr = DomainRulesManager()
    seed = "https://example.com/somesubject"
    # Discovered on a POST page of the same host, pointing to ANOTHER model.
    got = mgr.is_detail_page(
        "https://example.com/othermodel", seed, "somesubject", ["somesubject"]
    )
    assert got is False


def test_utility_link_blocked_at_depth1():
    """Utility/nav links (/login, /dmca) must be rejected regardless of depth."""
    mgr = DomainRulesManager()
    seed = "https://example.com/somesubject"
    for nav in ("login", "dmca", "privacy", "terms"):
        got = mgr.is_detail_page(
            f"https://example.com/{nav}", seed, "somesubject", ["somesubject"]
        )
        assert got is False, f"{nav} should be blocked"


def test_subject_post_allowed_at_depth1():
    """A subject's own content post must remain allowed at any depth."""
    mgr = DomainRulesManager()
    seed = "https://example.com/somesubject"
    for path in ("somesubject/9627870", "somesubject/9627870/2", "somesubject/Photos"):
        got = mgr.is_detail_page(
            f"https://example.com/{path}", seed, "somesubject", ["somesubject"]
        )
        assert got is True, f"{path} should be allowed"


def test_locale_prefixed_profile_seed_still_enforces_scope():
    """A locale-prefixed profile seed (/zh/somesubject) must collapse to its
    canonical bare form via normalize_url so the profile-scope rule fires and
    blocks an off-model link. The coordinator normalises seed_for_host before
    calling is_detail_page, so this collapse is what makes the rule work in
    production when a locale-prefixed seed is present."""
    seed = "https://example.com/zh/somesubject"
    # normalize_url collapses the 2-char zh locale segment per the
    # config-driven URL_NORMALISATION_RULES (not hardcoded here).
    assert normalize_url(seed) == "https://example.com/somesubject"
    mgr = DomainRulesManager()
    got = mgr.is_detail_page(
        "https://example.com/othermodel",
        normalize_url(seed),
        "somesubject",
        ["somesubject"],
    )
    assert got is False
