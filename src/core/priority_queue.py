"""
priority_queue.py — Best-First adaptive priority crawl queue and domain budget governor (v0.27.0).
"""

from __future__ import annotations

import heapq
import math
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from monitoring.logger import get_logger

LOGGER = get_logger(__name__)


class URLPatternBandit:
    """
    Multi-Armed Bandit (MAB) for URL path archetypes.
    Canonicalizes URLs into structural archetypes (e.g. 'domain.com::/gallery/{id}').
    Tracks trials (pages visited) and rewards (media harvested).
    Computes dynamic UCB1 score bonuses and dead-end penalties.
    """

    def __init__(self, exploration_weight: float = 1.414, max_bonus: float = 25.0):
        self.exploration_weight = exploration_weight
        self.max_bonus = max_bonus
        self._counts: Dict[str, int] = {}
        self._rewards: Dict[str, float] = {}
        self._total_trials = 0
        self._lock = threading.RLock()

    @staticmethod
    def extract_archetype(url: str) -> str:
        """
        Normalize a URL into its structural path archetype.
        e.g. 'https://example.com/gallery/12345/view' -> 'example.com::/gallery/{id}/view'
        """
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower().strip()
            path = parsed.path or "/"
            # Replace UUIDs
            path = re.sub(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", "{uuid}", path, flags=re.I)
            # Replace long hex/hashes (32+ chars)
            path = re.sub(r"[a-f0-9]{32,}", "{hash}", path, flags=re.I)
            # Replace numeric IDs
            path = re.sub(r"\b\d+\b", "{id}", path)
            return f"{host}::{path}"
        except Exception:
            return "unknown"

    @staticmethod
    def extract_prefix_archetype(url: str) -> str:
        """
        Extract coarse section archetype (e.g. 'example.com::/gallery/*').
        """
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower().strip()
            parts = [p for p in (parsed.path or "/").split("/") if p]
            if parts:
                return f"{host}::/{parts[0]}/*"
            return f"{host}::/*"
        except Exception:
            return "unknown"

    def record_harvest(self, url: str, media_yield: int) -> None:
        """Record the media yield outcome of a crawled page."""
        archetype = self.extract_archetype(url)
        prefix_archetype = self.extract_prefix_archetype(url)
        with self._lock:
            self._total_trials += 1
            reward = min(10.0, float(max(0, media_yield)))

            self._counts[archetype] = self._counts.get(archetype, 0) + 1
            self._rewards[archetype] = self._rewards.get(archetype, 0.0) + reward

            if prefix_archetype != archetype:
                self._counts[prefix_archetype] = self._counts.get(prefix_archetype, 0) + 1
                self._rewards[prefix_archetype] = self._rewards.get(prefix_archetype, 0.0) + reward

    def score_adjustment(self, url: str) -> float:
        """
        Compute priority score adjustment (-25.0 to +max_bonus) for this URL archetype.
        - High-yield archetypes get a positive boost.
        - Consistently zero-yield archetypes get a penalty.
        - Unexplored archetypes return 0.0 (neutral).
        """
        archetype = self.extract_archetype(url)
        with self._lock:
            key = archetype
            n = self._counts.get(key, 0)
            if n == 0:
                prefix_key = self.extract_prefix_archetype(url)
                if self._counts.get(prefix_key, 0) > 0:
                    key = prefix_key
                    n = self._counts[key]
                else:
                    return 0.0

            total = max(1, self._total_trials)
            mean_reward = self._rewards.get(key, 0.0) / n

            # Dead-end penalty: after 3+ visits with 0 yield
            if mean_reward == 0.0 and n >= 3:
                penalty = min(25.0, 5.0 * n)
                return -penalty

            # UCB1 bonus for promising paths
            exploration = self.exploration_weight * math.sqrt(math.log(total) / n)
            bonus = min(self.max_bonus, (mean_reward * 2.5) + (exploration * 1.5))
            return round(bonus, 4)


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
        pattern_bandit: Optional[URLPatternBandit] = None,
    ):
        self.w_depth = w_depth
        self.w_yield = w_yield
        self.w_token = w_token
        self.depth_lambda = depth_lambda
        self.pattern_bandit = pattern_bandit or URLPatternBandit()
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

        # 4. Multi-Armed Bandit Pattern Archetype adjustment
        pattern_adj = 0.0
        if self.pattern_bandit is not None:
            pattern_adj = self.pattern_bandit.score_adjustment(url)

        composite = depth_score + yield_score + token_score + pattern_adj - budget_penalty
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
