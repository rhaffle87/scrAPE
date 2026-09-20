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
