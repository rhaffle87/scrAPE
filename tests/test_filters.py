from core.filters import should_keep_image, should_keep_video
from core.models import ImageItem, VideoItem


def test_should_keep_image_rejects_generic_assets() -> None:
    item = ImageItem(
        url="https://example.com/assets/blank.gif",
        source_page="https://example.com/page",
        alt_text="",
    )
    assert should_keep_image(item, "subject") is False


def test_should_keep_image_accepts_keyword_related_image() -> None:
    item = ImageItem(
        url="https://example.com/subject-portrait.jpg",
        source_page="https://example.com/page",
        alt_text="Subject portrait image",
    )
    assert should_keep_image(item, "subject") is True


def test_should_keep_video_accepts_keyword_related_video() -> None:
    item = VideoItem(
        url="https://example.com/subject-demo.mp4",
        source_page="https://example.com/subject",
        type="direct",
    )
    assert should_keep_video(item, "subject") is True


def test_should_keep_image_rejects_thumbnail_like_urls() -> None:
    item = ImageItem(
        url="https://example.com/thumbs/subject-200x200.jpg",
        source_page="https://example.com/subject",
        alt_text="thumbnail",
    )
    assert should_keep_image(item, "subject") is False


def test_should_keep_image_rejects_low_resolution_size_hints() -> None:
    item = ImageItem(
        url="https://example.com/image.jpg?width=120&height=120",
        source_page="https://example.com/subject",
        alt_text="Subject costume",
    )
    assert should_keep_image(item, "subject") is False


def test_should_keep_image_accepts_subject_name_in_source() -> None:
    item = ImageItem(
        url="https://example.com/perfect.jpg",
        source_page="https://example.com/alias_beta-gallery",
        alt_text="Official shoot",
    )
    assert should_keep_image(item, "subject", entity_tokens=["alias_beta"]) is True


def test_should_keep_video_rejects_unrelated_video() -> None:
    item = VideoItem(
        url="https://example.com/celebrity_interview.mp4",
        source_page="https://example.com/entertainment",
        type="direct",
    )
    assert should_keep_video(item, "subject") is False


def test_manifest_driven_media_type_gating_and_boost() -> None:
    from core.filters import (
        is_cdn_asset_domain,
        media_type_matches_domain_expectation,
        score_image_relevance,
        score_video_relevance,
        rejection_reason_for_image,
        rejection_reason_for_video,
    )
    from core.seed_manifest import DomainProfile

    # Create dummy domain profiles:
    # 1. image-only domain: expects images, rejects videos
    # 2. video-only domain: expects videos, rejects images
    # 3. mixed domain: accepts both
    profiles = {
        "images.example-subject.com": DomainProfile(
            domain="images.example-subject.com",
            media_type="image",
            crawl_strategy="direct",
            crawl_depth=0,
            cdn_hosts=["cdn.example-subject.com", "cdn.other.com"],
        ),
        "videos.example-subject.com": DomainProfile(
            domain="videos.example-subject.com",
            media_type="video",
            crawl_strategy="index->detail",
            crawl_depth=1,
            cdn_hosts=[],
        ),
    }

    # Test CDN check
    allowed_hosts = ["cdn.example-subject.com"]
    assert (
        is_cdn_asset_domain(
            "https://cdn.example-subject.com/asset.jpg", allow_hosts=allowed_hosts
        )
        is True
    )
    assert (
        is_cdn_asset_domain(
            "https://unrelated.com/asset.jpg", allow_hosts=allowed_hosts
        )
        is False
    )
    assert (
        is_cdn_asset_domain(
            "https://cdn.example-subject.com/asset.jpg", allow_hosts=None
        )
        is False
    )

    # Test Media Gating:
    # Image on image domain -> Keep
    img_ok = ImageItem(
        url="https://example.com/subject.jpg",
        source_page="https://images.example-subject.com/gallery",
    )
    assert media_type_matches_domain_expectation(img_ok, profiles) is True
    assert (
        rejection_reason_for_image(img_ok, "subject", domain_profiles=profiles) is None
    )

    # Video on image domain -> Reject
    vid_bad = VideoItem(
        url="https://example.com/subject.mp4",
        source_page="https://images.example-subject.com/gallery",
        type="direct",
    )
    assert media_type_matches_domain_expectation(vid_bad, profiles) is False
    assert (
        rejection_reason_for_video(vid_bad, "subject", domain_profiles=profiles)
        == "wrong_media_type_for_domain"
    )

    # Image on video domain -> Reject
    img_bad = ImageItem(
        url="https://example.com/subject.jpg",
        source_page="https://videos.example-subject.com/page",
    )
    assert media_type_matches_domain_expectation(img_bad, profiles) is False
    assert (
        rejection_reason_for_image(img_bad, "subject", domain_profiles=profiles)
        == "wrong_media_type_for_domain"
    )

    # Video on video domain -> Keep
    vid_ok = VideoItem(
        url="https://example.com/subject.mp4",
        source_page="https://videos.example-subject.com/page",
        type="direct",
    )
    assert media_type_matches_domain_expectation(vid_ok, profiles) is True
    assert (
        rejection_reason_for_video(vid_ok, "subject", domain_profiles=profiles) is None
    )

    # Scoring Boost check:
    # Image on image domain gets +3 boost
    score_with_boost = score_image_relevance(
        img_ok, "subject", domain_profiles=profiles
    )
    score_without_boost = score_image_relevance(img_ok, "subject", domain_profiles=None)
    assert score_with_boost == score_without_boost + 3

    # Video on video domain gets +3 boost
    vscore_with_boost = score_video_relevance(
        vid_ok, "subject", domain_profiles=profiles
    )
    vscore_without_boost = score_video_relevance(
        vid_ok, "subject", domain_profiles=None
    )
    assert vscore_with_boost == vscore_without_boost + 3

    # CDN Dynamic Allow-List check:
    # A CDN asset on an archive page should bypass the index page penalty.
    cdn_img = ImageItem(
        url="https://cdn.other.com/asset.jpg",
        source_page="https://images.example-subject.com/page/2",
        alt_text="Some text",
        page_title="Archives",
    )
    score_with_profiles = score_image_relevance(
        cdn_img, "subject", domain_profiles=profiles
    )
    score_without_profiles = score_image_relevance(
        cdn_img, "subject", domain_profiles=None
    )
    # score_with_profiles gets +3 media boost AND bypasses the -15 archive penalty.
    assert score_with_profiles == score_without_profiles + 18


def test_normalize_media_url() -> None:
    from core.filters import normalize_media_url

    assert (
        normalize_media_url("http://example.com/image.jpg?w=100&h=200")
        == "https://example.com/image.jpg"
    )
    assert (
        normalize_media_url("https://example.com/video.mp4/")
        == "https://example.com/video.mp4"
    )
    assert (
        normalize_media_url("https://example.com/Video.MP4?token=abc")
        == "https://example.com/video.mp4"
    )


def test_thumbnail_prefix_pattern_filter() -> None:
    from core.filters import rejection_reason_for_image
    from core.seed_manifest import DomainProfile

    profiles = {
        "example.com": DomainProfile(
            domain="example.com",
            media_type="image",
            thumbnail_prefix_pattern=r"-\d+x\d+\.",
        ),
        "thumbs.com": DomainProfile(
            domain="thumbs.com",
            media_type="image",
            thumbnail_prefix_pattern=r"/thumbs/",
        ),
    }

    # Matches pattern -> preview_or_thumbnail
    item1 = ImageItem(
        url="https://example.live/uploads/post-320x180.jpg",
        source_page="https://example.com/page",
    )
    assert (
        rejection_reason_for_image(item1, "subject", domain_profiles=profiles)
        == "preview_or_thumbnail"
    )

    # Does not match pattern -> not preview_or_thumbnail
    item2 = ImageItem(
        url="https://example.live/uploads/post.jpg",
        source_page="https://example.com/page",
    )
    assert (
        rejection_reason_for_image(item2, "subject", domain_profiles=profiles)
        != "preview_or_thumbnail"
    )

    # example thumbs match -> preview_or_thumbnail
    item3 = ImageItem(
        url="https://m2.example.com/thumbs/123/subject.jpg",
        source_page="https://thumbs.com/artist/subject/",
    )
    assert (
        rejection_reason_for_image(item3, "subject", domain_profiles=profiles)
        == "preview_or_thumbnail"
    )


def test_extract_background_image() -> None:
    from core.filters import extract_background_image

    assert (
        extract_background_image("background-image: url('https://example.com/1.jpg')")
        == "https://example.com/1.jpg"
    )
    assert (
        extract_background_image(
            'background: transparent url("https://example.com/2.jpg") no-repeat'
        )
        == "https://example.com/2.jpg"
    )
    assert (
        extract_background_image(
            "background: url(https://example.com/3.jpg) no-repeat scroll 0px 0px"
        )
        == "https://example.com/3.jpg"
    )
    assert (
        extract_background_image(
            "color: red; background-image: url(https://example.com/4.jpg); width: 100px;"
        )
        == "https://example.com/4.jpg"
    )
    assert extract_background_image("color: blue;") is None
