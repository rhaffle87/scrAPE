"""
priority_queue.py — Best-First adaptive priority crawl queue and domain budget governor (v0.27.0).
"""

from __future__ import annotations

import heapq
import math
import re
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from monitoring.logger import get_logger

LOGGER = get_logger(__name__)


class DomainBudgetGovernor:
    """
    Tracks page crawl counts per domain and governs quota budgets:
    - 0% - 79%: Normal priority, 0 penalty.
    - 80% - 99%: Graceful quota de-prioritization (-50.0 score penalty).
    - 100%+: Hard stop / quota capped.
    """

    def __init__(self):
        self.domain_counts: Dict[str, int] = {}

    def record_page(self, domain: str) -> int:
        """Increment and return the total page count scanned for *domain*."""
        domain_clean = domain.lower().strip()
        self.domain_counts[domain_clean] = self.domain_counts.get(domain_clean, 0) + 1
        return self.domain_counts[domain_clean]

    def get_domain_count(self, domain: str) -> int:
        """Return the current page count for *domain*."""
        return self.domain_counts.get(domain.lower().strip(), 0)

    def is_domain_capped(self, domain: str, max_pages: Optional[int]) -> bool:
        """Check whether *domain* has reached or exceeded its maximum allocated page budget."""
        if max_pages is None or max_pages <= 0:
            return False
        return self.get_domain_count(domain) >= max_pages

    def get_budget_penalty(self, domain: str, max_pages: Optional[int]) -> float:
        """
        Compute budget penalty for priority scoring:
        - Returns 0.0 if under 80% of budget or budget unbounded.
        - Returns 50.0 if between 80% and 99% of budget.
        - Returns 1000.0 if at or above 100% of budget.
        """
        if max_pages is None or max_pages <= 0:
            return 0.0
        count = self.get_domain_count(domain)
        ratio = count / max_pages
        if ratio >= 1.0:
            return 1000.0
        if ratio >= 0.8:
            return 50.0
        return 0.0


class AdaptiveCrawlQueue:
    """
    Best-First adaptive priority queue for web crawling.
    Prioritizes URLs using a composite score:
      S(u) = w_depth * exp(-lambda * depth) + w_yield * YieldRatio(host)
             + w_token * TokenRelevance(u, keyword) - BudgetPenalty(host)

    Heap elements are stored as (-score, depth, retry_count, release_at, time_enqueued, url)
    so that the highest composite score is popped first.
    """

    def __init__(
        self,
        w_depth: float = 40.0,
        w_yield: float = 30.0,
        w_token: float = 30.0,
        depth_lambda: float = 0.5,
    ):
        self.w_depth = w_depth
        self.w_yield = w_yield
        self.w_token = w_token
        self.depth_lambda = depth_lambda
        self._heap: List[Tuple[float, int, int, float, float, str]] = []

    def calculate_score(
        self,
        url: str,
        depth: int,
        host_yield_ratio: float = 0.0,
        keyword: str = "",
        budget_penalty: float = 0.0,
    ) -> float:
        """Compute composite priority score for a candidate URL."""
        # 1. Depth exponential decay
        depth_score = self.w_depth * math.exp(-self.depth_lambda * max(0, depth))

        # 2. Host historical yield density bonus
        yield_score = self.w_yield * max(0.0, min(1.0, host_yield_ratio))

        # 3. Token relevance matching
        token_score = 0.0
        if keyword:
            kw_tokens = {tok.lower() for tok in re.findall(r"\w+", keyword) if len(tok) > 2}
            if kw_tokens:
                parsed = urlparse(url)
                url_tokens = {tok.lower() for tok in re.findall(r"\w+", f"{parsed.path} {parsed.query}") if len(tok) > 2}
                overlap = len(kw_tokens.intersection(url_tokens))
                token_ratio = overlap / len(kw_tokens)
                token_score = self.w_token * token_ratio

        composite = depth_score + yield_score + token_score - budget_penalty
        return round(composite, 4)

    def push(
        self,
        url: str,
        depth: int,
        retry_count: int = 0,
        release_at: float = 0.0,
        score: Optional[float] = None,
        host_yield_ratio: float = 0.0,
        keyword: str = "",
        budget_penalty: float = 0.0,
    ) -> float:
        """Push a URL onto the priority queue. Computes score if not explicitly given."""
        if score is None:
            score = self.calculate_score(
                url=url,
                depth=depth,
                host_yield_ratio=host_yield_ratio,
                keyword=keyword,
                budget_penalty=budget_penalty,
            )
        now = time.monotonic()
        # Inverted score for min-heap: highest score has most negative value -> popped first
        item = (-score, depth, retry_count, release_at, now, url)
        heapq.heappush(self._heap, item)
        return score

    def pop(self) -> Tuple[float, int, int, float, float, str]:
        """Pop and return (score, depth, retry_count, release_at, time_enqueued, url)."""
        neg_score, depth, retry_count, release_at, time_enqueued, url = heapq.heappop(self._heap)
        return (-neg_score, depth, retry_count, release_at, time_enqueued, url)

    def peek(self) -> Optional[Tuple[float, int, int, float, float, str]]:
        """Peek at the highest-priority item without popping."""
        if not self._heap:
            return None
        neg_score, depth, retry_count, release_at, time_enqueued, url = self._heap[0]
        return (-neg_score, depth, retry_count, release_at, time_enqueued, url)

    def __len__(self) -> int:
        return len(self._heap)

    def __bool__(self) -> bool:
        return len(self._heap) > 0

    def clear(self) -> None:
        """Clear all entries in the queue."""
        self._heap.clear()

    def snapshot(self) -> List[Tuple[float, int, int, float, float, str]]:
        """Return an unpacked snapshot list of items in the queue."""
        return [
            (-item[0], item[1], item[2], item[3], item[4], item[5])
            for item in self._heap
        ]

    def to_checkpoint_items(self) -> List[Dict[str, Any]]:
        """Serialize current queue contents for persistence in StateCache."""
        items = []
        for neg_score, depth, retry_count, release_at, time_enqueued, url in self._heap:
            items.append({
                "url": url,
                "depth": depth,
                "retry_count": retry_count,
                "score": round(-neg_score, 4),
            })
        return items

    def from_checkpoint_items(self, items: List[Dict[str, Any]]) -> int:
        """Restore queue items from StateCache checkpoint rows."""
        count = 0
        for it in items:
            url = it.get("url", "")
            if not url:
                continue
            depth = it.get("depth", 0)
            retry_count = it.get("retry_count", 0)
            score = it.get("score", 0.0)
            self.push(url=url, depth=depth, retry_count=retry_count, release_at=0.0, score=score)
            count += 1
        return count
