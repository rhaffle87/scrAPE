"""
stealth_fingerprint.py — Deterministic Sticky Per-Domain Hardware Stealth Fingerprinting.

Generates reproducible, domain-bound browser hardware emulation profiles and evasion scripts:
  - WebGL: GPU Vendor & Renderer spoofing (NVIDIA, AMD, Apple, Intel)
  - Canvas 2D: Sub-perceptual deterministic LSB pixel noise
  - AudioContext: Deterministic micro-latency and frequency buffer perturbation
  - WebRTC: Host candidate SDP filtering to eliminate local/intranet IP leaks
  - Navigator: Consistent hardwareConcurrency, deviceMemory, and webdriver masking
"""

from __future__ import annotations

import functools
import hashlib
import json
from typing import Any

from monitoring.logger import get_logger

logger = get_logger(__name__)

HARDWARE_PROFILES: list[dict[str, Any]] = [
    {
        "vendor": "Google Inc. (NVIDIA)",
        "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "unmasked_vendor": "Google Inc. (NVIDIA)",
        "unmasked_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "platform": "Win32",
        "hardware_concurrency": 16,
        "device_memory": 16,
        "gl_version": "WebGL 2.0 (OpenGL ES 3.0 Chromium)",
        "shading_language_version": "WebGL GLSL ES 3.00 (OpenGL ES Runtime)",
    },
    {
        "vendor": "Google Inc. (NVIDIA)",
        "renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "unmasked_vendor": "Google Inc. (NVIDIA)",
        "unmasked_renderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "platform": "Win32",
        "hardware_concurrency": 12,
        "device_memory": 16,
        "gl_version": "WebGL 2.0 (OpenGL ES 3.0 Chromium)",
        "shading_language_version": "WebGL GLSL ES 3.00 (OpenGL ES Runtime)",
    },
    {
        "vendor": "Google Inc. (AMD)",
        "renderer": "ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "unmasked_vendor": "Google Inc. (AMD)",
        "unmasked_renderer": "ANGLE (AMD, AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "platform": "Win32",
        "hardware_concurrency": 8,
        "device_memory": 16,
        "gl_version": "WebGL 2.0 (OpenGL ES 3.0 Chromium)",
        "shading_language_version": "WebGL GLSL ES 3.00 (OpenGL ES Runtime)",
    },
    {
        "vendor": "Google Inc. (Intel)",
        "renderer": "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "unmasked_vendor": "Google Inc. (Intel)",
        "unmasked_renderer": "ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)",
        "platform": "Win32",
        "hardware_concurrency": 8,
        "device_memory": 8,
        "gl_version": "WebGL 2.0 (OpenGL ES 3.0 Chromium)",
        "shading_language_version": "WebGL GLSL ES 3.00 (OpenGL ES Runtime)",
    },
    {
        "vendor": "Apple Inc.",
        "renderer": "Apple M2 Pro",
        "unmasked_vendor": "Apple Inc.",
        "unmasked_renderer": "Apple M2 Pro",
        "platform": "MacIntel",
        "hardware_concurrency": 12,
        "device_memory": 16,
        "gl_version": "WebGL 2.0 (OpenGL ES 3.0 Chromium)",
        "shading_language_version": "WebGL GLSL ES 3.00 (OpenGL ES Runtime)",
    },
    {
        "vendor": "Apple Inc.",
        "renderer": "Apple M1 Max",
        "unmasked_vendor": "Apple Inc.",
        "unmasked_renderer": "Apple M1 Max",
        "platform": "MacIntel",
        "hardware_concurrency": 10,
        "device_memory": 32,
        "gl_version": "WebGL 2.0 (OpenGL ES 3.0 Chromium)",
        "shading_language_version": "WebGL GLSL ES 3.00 (OpenGL ES Runtime)",
    },
]


class StealthFingerprintGenerator:
    """Generates deterministic, sticky browser hardware fingerprints and evasion injection scripts per domain."""

    @classmethod
    def get_fingerprint(cls, domain: str) -> dict[str, Any]:
        """Derive a deterministic hardware profile dictionary for *domain*."""
        norm_domain = (domain or "").strip().lower()
        seed_bytes = hashlib.sha256(norm_domain.encode("utf-8")).digest()
        seed_int = int.from_bytes(seed_bytes[:8], "big")

        idx = seed_int % len(HARDWARE_PROFILES)
        profile = HARDWARE_PROFILES[idx].copy()
        profile["domain"] = norm_domain
        profile["seed"] = seed_int
        profile["noise_seed"] = (seed_int % 99991) + 1
        # Audio jitter in range [-5e-6, 5e-6]
        profile["audio_jitter"] = round(((seed_int % 101) - 50) * 1e-7, 9)
        return profile

    @classmethod
    @functools.lru_cache(maxsize=256)
    def generate_stealth_script(cls, domain: str) -> str:
        """Produce self-executing JavaScript to inject via CDP Page.addScriptToEvaluateOnNewDocument."""
        profile = cls.get_fingerprint(domain)

        unmasked_vendor = json.dumps(profile["unmasked_vendor"])
        unmasked_renderer = json.dumps(profile["unmasked_renderer"])
        vendor = json.dumps(profile["vendor"])
        renderer = json.dumps(profile["renderer"])
        gl_version = json.dumps(profile["gl_version"])
        shading_lang = json.dumps(profile["shading_language_version"])
        hw_concurrency = int(profile["hardware_concurrency"])
        dev_memory = int(profile["device_memory"])
        noise_seed = int(profile["noise_seed"])
        audio_jitter = profile["audio_jitter"]

        return f"""// [scrAPE Sticky Stealth Fingerprint — Domain: {profile["domain"]}]
(function() {{
  'use strict';
  try {{
    // 1. WebGL & WebGL2 Parameter Masking
    const spoofParams = {{
      37445: {unmasked_vendor},    // UNMASKED_VENDOR_WEBGL
      37446: {unmasked_renderer},  // UNMASKED_RENDERER_WEBGL
      7936:  {vendor},             // VENDOR
      7937:  {renderer},           // RENDERER
      7938:  {gl_version},         // VERSION
      35724: {shading_lang}        // SHADING_LANGUAGE_VERSION
    }};

    const patchWebGL = (proto) => {{
      if (!proto || !proto.getParameter) return;
      const origGetParameter = proto.getParameter;
      proto.getParameter = function(param) {{
        if (param in spoofParams) {{
          return spoofParams[param];
        }}
        return origGetParameter.apply(this, arguments);
      }};
    }};

    if (window.WebGLRenderingContext) {{
      patchWebGL(WebGLRenderingContext.prototype);
    }}
    if (window.WebGL2RenderingContext) {{
      patchWebGL(WebGL2RenderingContext.prototype);
    }}

    // 2. Canvas 2D Sub-Perceptual Noise Injection
    if (window.CanvasRenderingContext2D) {{
      const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
      CanvasRenderingContext2D.prototype.getImageData = function(...args) {{
        const imgData = origGetImageData.apply(this, args);
        const d = imgData.data;
        const len = Math.min(d.length, 256);
        const seed = {noise_seed};
        for (let i = 0; i < len; i += 4) {{
          const offset = ((i * 3 + seed) % 3) - 1; // -1, 0, or 1
          d[i] = Math.max(0, Math.min(255, d[i] + offset));
        }}
        return imgData;
      }};
    }}

    // 3. AudioContext Latency & Frequency Micro-Perturbation
    const audioJitter = {audio_jitter};
    if (window.AnalyserNode) {{
      const origGetFloatFreq = AnalyserNode.prototype.getFloatFrequencyData;
      AnalyserNode.prototype.getFloatFrequencyData = function(array) {{
        origGetFloatFreq.apply(this, arguments);
        if (array && array.length) {{
          for (let i = 0; i < array.length; i += 8) {{
            array[i] += audioJitter;
          }}
        }}
      }};
    }}
    if (window.AudioBuffer) {{
      const origGetChannelData = AudioBuffer.prototype.getChannelData;
      AudioBuffer.prototype.getChannelData = function(...args) {{
        const channel = origGetChannelData.apply(this, args);
        if (channel && channel.length > 0) {{
          channel[0] += audioJitter;
        }}
        return channel;
      }};
    }}

    // 4. WebRTC Leak Protection (Suppress Private/Local Host Candidates)
    if (window.RTCPeerConnection) {{
      const origCreateOffer = RTCPeerConnection.prototype.createOffer;
      RTCPeerConnection.prototype.createOffer = function(...args) {{
        return origCreateOffer.apply(this, args).then(offer => {{
          if (offer && offer.sdp) {{
            offer.sdp = offer.sdp.replace(/a=candidate:.*?host.*?\r\n/g, '');
          }}
          return offer;
        }});
      }};
    }}

    // 5. Consistent Navigator Emulation
    try {{
      Object.defineProperty(navigator, 'webdriver', {{
        get: () => undefined,
        configurable: true
      }});
      Object.defineProperty(navigator, 'hardwareConcurrency', {{
        get: () => {hw_concurrency},
        configurable: true
      }});
      Object.defineProperty(navigator, 'deviceMemory', {{
        get: () => {dev_memory},
        configurable: true
      }});
    }} catch (navErr) {{}}

  }} catch (e) {{}}
}})();
"""


def get_stealth_script(domain: str) -> str:
    """Module-level helper to obtain cached stealth injection script for *domain*."""
    return StealthFingerprintGenerator.generate_stealth_script(domain)
