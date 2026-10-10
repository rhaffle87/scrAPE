"""
priority_queue.py — Best-First adaptive priority crawl queue and domain budget governor (v0.27.0).
"""

from __future__ import annotations

from functools import lru_cache
import heapq
import math
import re
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from monitoring.logger import get_logger

LOGGER = get_logger(__name__)

UUID_RE = re.compile(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}", re.I)
HEX_HASH_RE = re.compile(r"[a-f0-9]{32,}", re.I)
NUMERIC_ID_RE = re.compile(r"\b\d+\b")
TOKEN_WORD_RE = re.compile(r"\w+")


@lru_cache(maxsize=32)
def _tokenize_text(text: str) -> frozenset[str]:
    if not text:
        return frozenset()
    return frozenset(tok.lower() for tok in TOKEN_WORD_RE.findall(text) if len(tok) > 2)


@lru_cache(maxsize=65536)
def _extract_archetype_cached(url: str) -> str:
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower().strip()
        path = parsed.path or "/"
        path = UUID_RE.sub("{uuid}", path)
        path = HEX_HASH_RE.sub("{hash}", path)
        path = NUMERIC_ID_RE.sub("{id}", path)
        return f"{host}::{path}"
    except Exception:
        return "unknown"


@lru_cache(maxsize=65536)
def _extract_prefix_archetype_cached(url: str) -> str:
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower().strip()
        parts = [p for p in (parsed.path or "/").split("/") if p]
        if parts:
            return f"{host}::/{parts[0]}/*"
        return f"{host}::/*"
    except Exception:
        return "unknown"


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
        return _extract_archetype_cached(url)

    @staticmethod
    def extract_prefix_archetype(url: str) -> str:
        """
        Extract coarse section archetype (e.g. 'example.com::/gallery/*').
        """
        return _extract_prefix_archetype_cached(url)

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
        self._delayed_heap: List[Tuple[float, float, int, int, float, str]] = []
        self._parked_by_host: Dict[str, List[Tuple[float, int, int, float, float, str]]] = {}

    def _promote_delayed(self, now: Optional[float] = None) -> None:
        """Promote delayed items whose release_at has passed into the ready heap."""
        if not self._delayed_heap:
            return
        current_time = time.monotonic() if now is None else now
        promoted = False
        while self._delayed_heap and self._delayed_heap[0][0] <= current_time:
            release_at, neg_score, depth, retry_count, time_enqueued, url = heapq.heappop(self._delayed_heap)
            self._heap.append((neg_score, depth, retry_count, release_at, time_enqueued, url))
            promoted = True
        if promoted:
            heapq.heapify(self._heap)

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
            kw_tokens = _tokenize_text(keyword)
            if kw_tokens:
                parsed = urlparse(url)
                url_tokens = _tokenize_text(f"{parsed.path} {parsed.query}")
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
        if release_at > now:
            # Route delayed item into _delayed_heap (sorted by release_at asc)
            heapq.heappush(self._delayed_heap, (release_at, -score, depth, retry_count, now, url))
        else:
            # Inverted score for min-heap: highest score has most negative value -> popped first
            heapq.heappush(self._heap, (-score, depth, retry_count, release_at, now, url))
        return score

    def requeue_batch(self, items: List[Tuple[float, int, int, float, float, str]]) -> None:
        """Efficiently batch-requeue unpacked tuples (score, depth, retry_count, release_at, time_enqueued, url)."""
        if not items:
            return
        now = time.monotonic()
        reheapify = False
        for score, depth, retry_count, release_at, time_enqueued, url in items:
            if release_at > now:
                heapq.heappush(self._delayed_heap, (release_at, -score, depth, retry_count, time_enqueued, url))
            else:
                self._heap.append((-score, depth, retry_count, release_at, time_enqueued, url))
                reheapify = True
        if reheapify:
            heapq.heapify(self._heap)

    def park_host(self, host: str, item: Tuple[float, int, int, float, float, str]) -> None:
        """Park an item under its host key while the host is saturated or cooling down."""
        clean = host.lower().strip() or "unknown"
        self._parked_by_host.setdefault(clean, []).append(item)

    def unpark_host(self, host: str) -> int:
        """Unpark all parked items for a specific host back into the ready/delayed queue."""
        clean = host.lower().strip() or "unknown"
        items = self._parked_by_host.pop(clean, None)
        if not items:
            return 0
        self.requeue_batch(items)
        return len(items)

    def unpark_all(self) -> int:
        """Unpark all parked items across all hosts back into the ready/delayed queue."""
        if not self._parked_by_host:
            return 0
        all_items: List[Tuple[float, int, int, float, float, str]] = []
        for items in self._parked_by_host.values():
            all_items.extend(items)
        self._parked_by_host.clear()
        self.requeue_batch(all_items)
        return len(all_items)

    def earliest_release_at(self) -> Optional[float]:
        """Return the earliest release_at timestamp for pending delayed items (or 0.0 if ready items exist)."""
        self._promote_delayed()
        if self._heap:
            return 0.0
        if self._delayed_heap:
            return self._delayed_heap[0][0]
        return None

    def pop(self) -> Tuple[float, int, int, float, float, str]:
        """Pop and return (score, depth, retry_count, release_at, time_enqueued, url)."""
        self._promote_delayed()
        if not self._heap and self._parked_by_host:
            self.unpark_all()
        if not self._heap and self._delayed_heap:
            release_at, neg_score, depth, retry_count, time_enqueued, url = heapq.heappop(self._delayed_heap)
            return (-neg_score, depth, retry_count, release_at, time_enqueued, url)
        if not self._heap:
            raise IndexError("pop from an empty AdaptiveCrawlQueue")
        neg_score, depth, retry_count, release_at, time_enqueued, url = heapq.heappop(self._heap)
        return (-neg_score, depth, retry_count, release_at, time_enqueued, url)

    def peek(self) -> Optional[Tuple[float, int, int, float, float, str]]:
        """Peek at the highest-priority item without popping."""
        self._promote_delayed()
        if not self._heap and self._parked_by_host:
            self.unpark_all()
        if self._heap:
            neg_score, depth, retry_count, release_at, time_enqueued, url = self._heap[0]
            return (-neg_score, depth, retry_count, release_at, time_enqueued, url)
        if self._delayed_heap:
            release_at, neg_score, depth, retry_count, time_enqueued, url = self._delayed_heap[0]
            return (-neg_score, depth, retry_count, release_at, time_enqueued, url)
        return None

    def __len__(self) -> int:
        return len(self._heap) + len(self._delayed_heap) + sum(len(v) for v in self._parked_by_host.values())

    def __bool__(self) -> bool:
        return len(self) > 0

    def clear(self) -> None:
        """Clear all entries across heap, delayed heap, and parked partitions."""
        self._heap.clear()
        self._delayed_heap.clear()
        self._parked_by_host.clear()

    def snapshot(self) -> List[Tuple[float, int, int, float, float, str]]:
        """Return an unpacked snapshot list of items in the queue."""
        self._promote_delayed()
        items = [
            (-item[0], item[1], item[2], item[3], item[4], item[5])
            for item in self._heap
        ]
        for rel, neg_score, depth, retry_count, time_enqueued, url in self._delayed_heap:
            items.append((-neg_score, depth, retry_count, rel, time_enqueued, url))
        for host_items in self._parked_by_host.values():
            items.extend(host_items)
        return items

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
        for rel, neg_score, depth, retry_count, time_enqueued, url in self._delayed_heap:
            items.append({
                "url": url,
                "depth": depth,
                "retry_count": retry_count,
                "score": round(-neg_score, 4),
            })
        for host_items in self._parked_by_host.values():
            for score, depth, retry_count, release_at, time_enqueued, url in host_items:
                items.append({
                    "url": url,
                    "depth": depth,
                    "retry_count": retry_count,
                    "score": round(score, 4),
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
