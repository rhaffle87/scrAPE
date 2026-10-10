"""
test_adaptive_priority_queue_and_budget.py — Unit tests for AdaptiveCrawlQueue and DomainBudgetGovernor (v0.27.0).
"""

from core.priority_queue import AdaptiveCrawlQueue, DomainBudgetGovernor


def test_domain_budget_governor_penalties_and_capping():
    """Verify DomainBudgetGovernor penalty stages and hard-capping."""
    gov = DomainBudgetGovernor()
    domain = "gallery.example.com"
    max_pages = 10

    # 0 to 7 pages: 0.0 penalty, not capped
    for _ in range(7):
        gov.record_page(domain)
    assert gov.get_domain_count(domain) == 7
    assert gov.get_budget_penalty(domain, max_pages) == 0.0
    assert not gov.is_domain_capped(domain, max_pages)

    # 8 pages: 80% -> 50.0 penalty, still not capped
    gov.record_page(domain)
    assert gov.get_domain_count(domain) == 8
    assert gov.get_budget_penalty(domain, max_pages) == 50.0
    assert not gov.is_domain_capped(domain, max_pages)

    # 9 pages: 90% -> 50.0 penalty, not capped
    gov.record_page(domain)
    assert gov.get_budget_penalty(domain, max_pages) == 50.0
    assert not gov.is_domain_capped(domain, max_pages)

    # 10 pages: 100% -> hard cap reached
    gov.record_page(domain)
    assert gov.get_domain_count(domain) == 10
    assert gov.get_budget_penalty(domain, max_pages) == 1000.0
    assert gov.is_domain_capped(domain, max_pages)


def test_adaptive_crawl_queue_scoring():
    """Verify composite scoring components: depth decay, yield bonus, keyword relevance, budget penalty."""
    q = AdaptiveCrawlQueue(w_depth=40.0, w_yield=30.0, w_token=30.0, depth_lambda=0.5)

    # Depth 0 with high yield and keyword match
    s_high = q.calculate_score(
        url="https://site.com/supercars/ferrari-488.html",
        depth=0,
        host_yield_ratio=0.9,
        keyword="supercars ferrari",
        budget_penalty=0.0,
    )

    # Depth 3 with zero yield and no keyword match
    s_low = q.calculate_score(
        url="https://site.com/about/contact-us.html",
        depth=3,
        host_yield_ratio=0.0,
        keyword="supercars ferrari",
        budget_penalty=0.0,
    )

    assert s_high > s_low
    assert s_high > 60.0
    assert s_low < 15.0

    # Test budget penalty deduction
    s_penalized = q.calculate_score(
        url="https://site.com/supercars/ferrari-488.html",
        depth=0,
        host_yield_ratio=0.9,
        keyword="supercars ferrari",
        budget_penalty=50.0,
    )
    assert round(s_high - s_penalized, 2) == 50.0


def test_adaptive_crawl_queue_priority_order():
    """Verify items are popped in descending order of composite score."""
    q = AdaptiveCrawlQueue()

    q.push(url="https://site.com/low", depth=3, score=10.0)
    q.push(url="https://site.com/high", depth=0, score=95.0)
    q.push(url="https://site.com/medium", depth=1, score=50.0)

    assert len(q) == 3
    peeked = q.peek()
    assert peeked is not None
    assert peeked[5] == "https://site.com/high"

    first = q.pop()
    assert first[5] == "https://site.com/high"
    assert first[0] == 95.0

    second = q.pop()
    assert second[5] == "https://site.com/medium"
    assert second[0] == 50.0

    third = q.pop()
    assert third[5] == "https://site.com/low"
    assert third[0] == 10.0

    assert len(q) == 0


def test_adaptive_crawl_queue_checkpoint_serialization():
    """Verify queue can serialize to and restore from checkpoint items."""
    q = AdaptiveCrawlQueue()
    q.push(url="https://site.com/p1", depth=1, retry_count=0, score=80.0)
    q.push(url="https://site.com/p2", depth=2, retry_count=1, score=45.0)

    items = q.to_checkpoint_items()
    assert len(items) == 2
    assert any(it["url"] == "https://site.com/p1" for it in items)

    new_q = AdaptiveCrawlQueue()
    restored_count = new_q.from_checkpoint_items(items)
    assert restored_count == 2
    assert len(new_q) == 2

    # Pop order preserved (highest score first)
    top = new_q.pop()
    assert top[5] == "https://site.com/p1"
    assert top[0] == 80.0


def test_url_pattern_bandit_archetype_extraction():
    """Verify URLPatternBandit extracts canonical path archetypes."""
    from core.priority_queue import URLPatternBandit
    bandit = URLPatternBandit()

    arch1 = bandit.extract_archetype("https://example.com/gallery/12345/view")
    assert arch1 == "example.com::/gallery/{id}/view"

    arch2 = bandit.extract_archetype("https://cdn.site.org/assets/c0ffee01-1234-5678-abcd-0123456789ab/pic.png")
    assert arch2 == "cdn.site.org::/assets/{uuid}/pic.png"

    arch3 = bandit.extract_archetype("https://img.host.net/raw/abcdef1234567890abcdef1234567890/item")
    assert arch3 == "img.host.net::/raw/{hash}/item"


def test_url_pattern_bandit_learning_and_scoring():
    """Verify bandit rewards high-yield archetypes and penalizes zero-yield dead-ends."""
    from core.priority_queue import URLPatternBandit, AdaptiveCrawlQueue
    bandit = URLPatternBandit()

    good_url1 = "https://site.com/gallery/100"
    good_url2 = "https://site.com/gallery/101"
    dead_url1 = "https://site.com/legal/terms"
    dead_url2 = "https://site.com/legal/privacy"
    dead_url3 = "https://site.com/legal/cookie-policy"

    # Initially neutral (0.0)
    assert bandit.score_adjustment(good_url1) == 0.0
    assert bandit.score_adjustment(dead_url1) == 0.0

    # Record good harvests for gallery archetype
    bandit.record_harvest(good_url1, media_yield=8)
    bandit.record_harvest(good_url2, media_yield=10)

    # Record repeated zero-yield harvests for legal archetype
    bandit.record_harvest(dead_url1, media_yield=0)
    bandit.record_harvest(dead_url2, media_yield=0)
    bandit.record_harvest(dead_url3, media_yield=0)

    # Gallery pattern should receive high boost
    good_boost = bandit.score_adjustment("https://site.com/gallery/102")
    assert good_boost > 10.0

    # Legal pattern should receive negative penalty
    dead_penalty = bandit.score_adjustment("https://site.com/legal/disclaimer")
    assert dead_penalty < 0.0

    # Test integration with AdaptiveCrawlQueue
    q = AdaptiveCrawlQueue(pattern_bandit=bandit)
    score_good = q.calculate_score("https://site.com/gallery/103", depth=1)
    score_dead = q.calculate_score("https://site.com/legal/dmca", depth=1)
    assert score_good > score_dead + 20.0


def test_adaptive_crawl_queue_delayed_partition():
    """Verify delayed heap partitions items until release_at passes."""
    import time
    q = AdaptiveCrawlQueue()
    now = time.monotonic()

    # Immediate item with lower score
    q.push(url="https://site.com/ready", depth=1, score=10.0, release_at=0.0)
    # Delayed item with higher score (1.5s in future)
    q.push(url="https://site.com/delayed", depth=0, score=90.0, release_at=now + 1.5)

    assert len(q) == 2
    # Peek should return the ready item because delayed is parked
    peeked = q.peek()
    assert peeked is not None
    assert peeked[5] == "https://site.com/ready"

    # Pop returns the ready item
    popped = q.pop()
    assert popped[5] == "https://site.com/ready"

    # Only delayed item remains
    assert len(q) == 1
    earliest = q.earliest_release_at()
    assert earliest is not None
    assert earliest > now

    # Promote delayed explicitly with simulated future timestamp
    q._promote_delayed(now=now + 2.0)
    assert q.earliest_release_at() == 0.0
    top = q.pop()
    assert top[5] == "https://site.com/delayed"
    assert top[0] == 90.0
    assert len(q) == 0


def test_adaptive_crawl_queue_host_parking_and_batch_requeue():
    """Verify per-host parking segregates saturated hosts and unparks efficiently."""
    import time
    q = AdaptiveCrawlQueue()
    now = time.monotonic()

    # Push items for host A and host B
    q.push(url="https://host-a.com/page1", depth=1, score=80.0)
    q.push(url="https://host-a.com/page2", depth=1, score=75.0)
    q.push(url="https://host-b.com/page1", depth=1, score=60.0)

    # Pop first item for host-a, park the second because host-a is saturated
    first = q.pop()
    assert first[5] == "https://host-a.com/page1"

    second = q.pop()
    assert second[5] == "https://host-a.com/page2"
    q.park_host("host-a.com", second)

    # Length still reflects total pending URLs
    assert len(q) == 2

    # Next pop is host-b because host-a is parked
    third = q.pop()
    assert third[5] == "https://host-b.com/page1"

    # Now unpark host-a when its worker completes
    unparked_count = q.unpark_host("host-a.com")
    assert unparked_count == 1
    assert len(q) == 1

    restored = q.pop()
    assert restored[5] == "https://host-a.com/page2"
    assert len(q) == 0

    # Test batch requeue
    batch = [
        (40.0, 1, 0, 0.0, now, "https://site.com/batch1"),
        (85.0, 1, 0, 0.0, now, "https://site.com/batch2"),
    ]
    q.requeue_batch(batch)
    assert len(q) == 2
    top = q.pop()
    assert top[5] == "https://site.com/batch2"
    assert top[0] == 85.0
