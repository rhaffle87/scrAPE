"""Unit tests for universal CAPTCHA providers and strategy selection."""

from unittest.mock import patch
from captcha.captcha_strategy import ThirdPartyCaptchaStrategy
from monitoring.hardware_governor import HardwareLoadGovernor


def test_third_party_captcha_strategy_preference():
    # 1. Test free_audio preference
    with patch("config.settings_manager.settings.get", side_effect=lambda k: "free_audio" if k == "CAPTCHA_PRIMARY_PROVIDER" else None):
        strategy = ThirdPartyCaptchaStrategy()
        # Should attempt to instantiate FreeAudioCaptchaProvider
        assert strategy.name == "third_party_captcha"

    # 2. Test 2captcha preference
    from captcha.captcha_solvers.twocaptcha_provider import TwoCaptchaProvider
    from captcha.captcha_solvers.anticaptcha_provider import AntiCaptchaProvider

    with patch("config.settings_manager.settings.get", side_effect=lambda k: "2captcha" if k == "CAPTCHA_PRIMARY_PROVIDER" else ("dummy_2cap_key" if k == "TWOCAPTCHA_API_KEY" else None)):
        strategy_2cap = ThirdPartyCaptchaStrategy()
        assert strategy_2cap.provider is not None
        assert isinstance(strategy_2cap.provider, TwoCaptchaProvider)

    # 3. Test anticaptcha preference
    with patch("config.settings_manager.settings.get", side_effect=lambda k: "anticaptcha" if k == "CAPTCHA_PRIMARY_PROVIDER" else ("dummy_anti_key" if k == "ANTICAPTCHA_API_KEY" else None)):
        strategy_anti = ThirdPartyCaptchaStrategy()
        assert strategy_anti.provider is not None
        assert isinstance(strategy_anti.provider, AntiCaptchaProvider)


def test_hardware_governor_node_health_metrics():
    gov = HardwareLoadGovernor()
    metrics = gov.get_metrics()
    assert "cpu_percent" in metrics
    assert "ram_percent_available" in metrics
    assert "disk_percent_available" in metrics
    assert 0.0 <= metrics["cpu_percent"] <= 100.0
    assert 0.0 <= metrics["ram_percent_available"] <= 100.0

    scale = gov.get_concurrency_scale_factor()
    assert 0.25 <= scale <= 1.0
