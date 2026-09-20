"""
test_utility_asset_split.py
Item B: UTILITY_ASSET_TERMS triggers hard rejection; GENERIC_ASSET_TERMS triggers
only a score penalty, not a hard reject.
"""
import pytest

from config import UTILITY_ASSET_TERMS, GENERIC_ASSET_TERMS
from core.models import ImageItem
from core.filters import rejection_reason_for_image, score_image_relevance


def _img(url, source_page="https://example.com/gallery/subject", alt="subject", title="subject gallery"):
    return ImageItem(url=url, source_page=source_page, alt_text=alt, page_title=title)


class TestUtilityAssetTerms:
    """UTILITY_ASSET_TERMS items must still trigger generic_asset hard rejection."""

    @pytest.mark.parametrize("term", sorted(UTILITY_ASSET_TERMS))
    def test_utility_term_triggers_hard_reject(self, term):
        url = f"https://example.com/assets/{term}.png"
        item = _img(url)
        reason = rejection_reason_for_image(item, "subject")
        # logo/icon/banner etc. in URL → must hard reject
        assert reason == "generic_asset", (
            f"Expected generic_asset for UTILITY_ASSET_TERMS term '{term}' but got: {reason!r}"
        )


class TestGenericAssetTermsSoftPenaltyOnly:
    """GENERIC_ASSET_TERMS items must NOT cause a hard rejection on their own.
    They should only contribute a score penalty.
    """

    @pytest.mark.parametrize("term", sorted(GENERIC_ASSET_TERMS))
    def test_generic_term_does_not_hard_reject(self, term):
        # On-subject URL — the term is in the path but subject token is strong
        url = f"https://example.com/subject/photo_{term}_fullsize.jpg"
        item = _img(url, alt="subject photo", title="subject gallery")
        reason = rejection_reason_for_image(item, "subject")
        assert reason != "generic_asset", (
            f"GENERIC_ASSET_TERMS term '{term}' must NOT cause hard rejection; got: {reason!r}"
        )

    @pytest.mark.parametrize("term", sorted(GENERIC_ASSET_TERMS))
    def test_generic_term_applies_score_penalty(self, term):
        url_with_term = f"https://example.com/subject/photo_{term}.jpg"
        url_clean = "https://example.com/subject/photo.jpg"
        item_with = _img(url_with_term)
        item_clean = _img(url_clean)
        score_with = score_image_relevance(item_with, "subject")
        score_clean = score_image_relevance(item_clean, "subject")
        assert score_with <= score_clean, (
            f"GENERIC_ASSET_TERMS term '{term}' should reduce score; "
            f"with={score_with} vs clean={score_clean}"
        )


class TestThumbnailNotHardRejected:
    """Regression: 'thumbnail' was previously in GENERIC_ASSET_TERMS and caused
    hard rejection. It must now be absent from UTILITY_ASSET_TERMS."""

    def test_thumbnail_not_in_utility_terms(self):
        assert "thumbnail" not in UTILITY_ASSET_TERMS, \
            "'thumbnail' must not be in UTILITY_ASSET_TERMS (would hard-reject on-subject images)"

    def test_on_subject_thumbnail_url_not_hard_rejected(self):
        item = _img(
            "https://cdn.example.com/subject/photo_thumbnail.jpg",
            alt="subject",
            title="subject gallery",
        )
        reason = rejection_reason_for_image(item, "subject")
        assert reason != "generic_asset", (
            f"On-subject 'thumbnail' URL must not hard-reject as generic_asset; got: {reason!r}"
        )
