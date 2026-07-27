"""
test_capsolver_integration.py — Unit tests for CapSolverStrategy and WAF auto-solving pipeline.
"""

import pytest
from unittest.mock import MagicMock
from utils.capsolver_strategy import CapSolverStrategy
from utils.stealth_pipeline import StealthPipeline, StealthResponse


def test_capsolver_strategy_availability():
    strategy_no_key = CapSolverStrategy(api_key="")
    assert strategy_no_key.is_available() is False

    strategy_with_key = CapSolverStrategy(api_key="TEST_KEY_123")
    assert strategy_with_key.is_available() is True


def test_capsolver_sitekey_extraction():
    strategy = CapSolverStrategy(api_key="TEST_KEY_123")

    html_turnstile = '<div class="cf-turnstile" data-sitekey="0x4AAAAAAATestKey12345"></div>'
    extracted = strategy._extract_sitekey(html_turnstile)
    assert extracted == "0x4AAAAAAATestKey12345"

    html_sitekey_param = 'sitekey: "0x4AAAAAAAAnotherKey999"'
    extracted_2 = strategy._extract_sitekey(html_sitekey_param)
    assert extracted_2 == "0x4AAAAAAAAnotherKey999"

    html_raw_token = 'turnstile.render("#container", { siteKey: "0x4AAAAAAABbbBbbb123456" });'
    extracted_3 = strategy._extract_sitekey(html_raw_token)
    assert extracted_3 == "0x4AAAAAAABbbBbbb123456"


def test_capsolver_strategy_execute_success(monkeypatch):
    strategy = CapSolverStrategy(api_key="TEST_KEY_123")

    mock_client = MagicMock()
    mock_client._is_cloudflare_challenge.side_effect = lambda html: "Just a moment..." in html

    # Initial response simulates a Cloudflare Turnstile challenge page
    initial_resp = MagicMock()
    initial_resp.text = '<html><title>Just a moment...</title><div data-sitekey="0x4AAAAAAATestKey"></div></html>'
    mock_client.client.get.side_effect = [
        initial_resp,
        # Retry response simulates cleared challenge page
        MagicMock(status_code=200, text="<html>Unlocked Content</html>", cookies={"cf_clearance": "cleared_val_123"}, headers={}),
    ]

    # Mock CapSolver Client solve_turnstile
    monkeypatch.setattr(strategy.client, "solve_turnstile", lambda website_url, website_key, timeout: "SOLVED_TOKEN_ABC")

    res = strategy.execute("https://mitaku.net/test", mock_client)
    assert res is not None
    assert res.status_code == 200
    assert res.text == "<html>Unlocked Content</html>"
    assert res.cookies == {"cf_clearance": "cleared_val_123"}
    assert res.strategy_name == "capsolver"
    mock_client._save_domain_cookies.assert_called_once()


def test_capsolver_strategy_fallback_when_disabled():
    strategy = CapSolverStrategy(api_key="")
    mock_client = MagicMock()
    res = strategy.execute("https://mitaku.net/test", mock_client)
    assert res is None
