"""
tests/network/test_stealth_hardware_fingerprinting.py — Unit tests for Sticky Per-Domain Hardware Stealth Fingerprinting.
"""

from __future__ import annotations

import pytest

from network.stealth_fingerprint import (
    HARDWARE_PROFILES,
    StealthFingerprintGenerator,
    get_stealth_script,
)
from network.browser_client import BrowserClientMixin


class DummyBrowserClient(BrowserClientMixin):
    """Minimal test harness for BrowserClientMixin."""

    pass


class TestStealthFingerprintGenerator:
    """Test suite for deterministic hardware profile and script generation."""

    def test_fingerprint_determinism_and_idempotence(self):
        """Verify the exact same profile is generated across multiple calls."""
        fp1 = StealthFingerprintGenerator.get_fingerprint("example.com")
        fp2 = StealthFingerprintGenerator.get_fingerprint("example.com")
        assert fp1 == fp2

        # Case insensitivity
        fp3 = StealthFingerprintGenerator.get_fingerprint("EXAMPLE.COM")
        assert fp1["vendor"] == fp3["vendor"]
        assert fp1["renderer"] == fp3["renderer"]
        assert fp1["noise_seed"] == fp3["noise_seed"]

    def test_fingerprint_structure_and_validity(self):
        """Verify all essential fingerprint fields are present and typed properly."""
        fp = StealthFingerprintGenerator.get_fingerprint("cloudflare.com")

        required_keys = [
            "vendor",
            "renderer",
            "unmasked_vendor",
            "unmasked_renderer",
            "platform",
            "hardware_concurrency",
            "device_memory",
            "gl_version",
            "shading_language_version",
            "noise_seed",
            "audio_jitter",
        ]
        for key in required_keys:
            assert key in fp, f"Missing key '{key}' in generated fingerprint"

        assert isinstance(fp["hardware_concurrency"], int)
        assert fp["hardware_concurrency"] in (8, 10, 12, 16)
        assert isinstance(fp["device_memory"], int)
        assert fp["device_memory"] in (8, 16, 32)
        assert isinstance(fp["noise_seed"], int)
        assert isinstance(fp["audio_jitter"], float)

    def test_fingerprint_entropy_across_domains(self):
        """Verify that distinct domains produce diverse seeds and varied profiles."""
        domains = [
            "google.com",
            "github.com",
            "news.ycombinator.com",
            "reddit.com",
            "amazon.com",
            "wikipedia.org",
            "apple.com",
            "cloudflare.com",
        ]
        profiles = [StealthFingerprintGenerator.get_fingerprint(d) for d in domains]
        unique_renderers = {p["renderer"] for p in profiles}
        unique_seeds = {p["seed"] for p in profiles}

        # Seeds must all be unique
        assert len(unique_seeds) == len(domains)
        # Should pick multiple distinct GPU profiles across 8 domains
        assert len(unique_renderers) > 1

    def test_script_generation_content_and_coverage(self):
        """Verify the generated JavaScript contains WebGL, Canvas, Audio, WebRTC, and Navigator patches."""
        script = StealthFingerprintGenerator.generate_stealth_script("target-site.org")
        assert isinstance(script, str)
        assert script.startswith("// [scrAPE Sticky Stealth Fingerprint — Domain: target-site.org]")

        # 1. WebGL spoofing
        assert "UNMASKED_VENDOR_WEBGL" in script
        assert "UNMASKED_RENDERER_WEBGL" in script
        assert "WebGLRenderingContext" in script
        assert "WebGL2RenderingContext" in script
        assert "getParameter" in script

        # 2. Canvas 2D noise
        assert "CanvasRenderingContext2D" in script
        assert "getImageData" in script

        # 3. AudioContext micro-perturbation
        assert "AnalyserNode" in script
        assert "getFloatFrequencyData" in script
        assert "AudioBuffer" in script
        assert "getChannelData" in script

        # 4. WebRTC leak prevention
        assert "RTCPeerConnection" in script
        assert "createOffer" in script
        assert "candidate" in script

        # 5. Navigator masking
        assert "hardwareConcurrency" in script
        assert "deviceMemory" in script
        assert "webdriver" in script

    def test_script_caching_and_helper(self):
        """Verify LRU cache and module-level helper behavior."""
        s1 = get_stealth_script("mytestdomain.com")
        s2 = get_stealth_script("mytestdomain.com")
        assert s1 is s2  # Exact cached object


class TestBrowserClientStealthIntegration:
    """Test suite for BrowserClientMixin integration with stealth fingerprinting."""

    def test_client_get_stealth_script_with_domain(self):
        client = DummyBrowserClient()
        script = client.get_stealth_script("example.com")
        assert "example.com" in script
        assert "UNMASKED_VENDOR_WEBGL" in script

    def test_client_get_stealth_script_with_url(self):
        client = DummyBrowserClient()
        script = client.get_stealth_script("https://api.scraper-test.com:8443/products?page=2")
        assert "api.scraper-test.com:8443" in script
        assert "hardwareConcurrency" in script
