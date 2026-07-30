"""
scratch/test_adaptive_jitter.py

Unit tests for _DomainCooldownState.adaptive_jitter() and the live-jitter
propagation in HttpClient._rate_limiter_for().
"""

from network.http_client import _DomainCooldownState
from config import RATE_LIMIT_JITTER_SECONDS


# ---------------------------------------------------------------------------
# adaptive_jitter() formula tests
# ---------------------------------------------------------------------------

def test_adaptive_jitter_baseline_zero_429s():
    """Zero 429s → jitter equals base constant."""
    state = _DomainCooldownState()
    assert state.adaptive_jitter() == RATE_LIMIT_JITTER_SECONDS


def test_adaptive_jitter_scales_with_429s():
    """Jitter grows +0.1 s per 429 hit."""
    state = _DomainCooldownState()
    state.total_429s = 5
    expected = round(RATE_LIMIT_JITTER_SECONDS + 5 * 0.1, 10)
    assert abs(state.adaptive_jitter() - expected) < 1e-9


def test_adaptive_jitter_hard_cap_at_2s():
    """Jitter is capped at 2.0 s regardless of 429 count."""
    state = _DomainCooldownState()
    state.total_429s = 1000
    assert state.adaptive_jitter() == 2.0


def test_record_429_increments_total_429s():
    """record_429() increments total_429s each call."""
    state = _DomainCooldownState()
    assert state.total_429s == 0
    state.record_429()
    state.record_429()
    state.record_429()
    assert state.total_429s == 3


def test_total_429s_never_resets_on_success():
    """record_success() resets consecutive counters but NOT total_429s."""
    state = _DomainCooldownState()
    state.record_429()
    state.record_429()
    state.record_success()
    assert state.total_429s == 2
    assert state.consecutive_429s == 0


# ---------------------------------------------------------------------------
# Integration: _rate_limiter_for live-jitter propagation
# ---------------------------------------------------------------------------

def test_rate_limiter_jitter_updates_after_429(tmp_path):
    """After a 429 is recorded, _rate_limiter_for propagates the new jitter."""
    import sys, pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

    from network.http_client import HttpClient

    client = HttpClient()
    url = "https://adaptive-jitter-test-domain.example/page"

    # Warm up the limiter with a fresh state (no 429s yet)
    rl_before = client._rate_limiter_for(url)
    jitter_before = rl_before.jitter

    # Simulate two 429 responses being recorded
    cd = client._cooldown_state_for(url)
    cd.record_429()
    cd.record_429()

    # Next call to _rate_limiter_for should push updated jitter into limiter
    rl_after = client._rate_limiter_for(url)
    expected_jitter = min(RATE_LIMIT_JITTER_SECONDS + 2 * 0.1, 2.0)

    assert rl_after.jitter > jitter_before
    assert abs(rl_after.jitter - expected_jitter) < 1e-9
