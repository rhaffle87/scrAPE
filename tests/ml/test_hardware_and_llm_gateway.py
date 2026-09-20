"""Unit tests for HardwareDeviceManager and Multi-Provider LLM Gateway in SelfHealingDOMParser."""

from unittest.mock import MagicMock, patch
from ml.hardware import HardwareDeviceManager, get_hardware_manager
from core.self_healing_parser import SelfHealingDOMParser


def test_hardware_device_manager():
    mgr = HardwareDeviceManager()
    assert mgr.device in ("cpu", "cuda", "mps", "privateuseone")
    assert mgr.dtype in ("float32", "float16")
    info = mgr.get_device_info()
    assert "device" in info
    assert "dtype" in info
    assert "is_gpu" in info

    singleton = get_hardware_manager()
    assert singleton is not None


def test_llm_gateway_ollama_mock(tmp_path):
    parser = SelfHealingDOMParser(db_path=str(tmp_path / "test.db"), llm_provider="ollama")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"response": '{"selector": ".main-image", "attribute": "src"}'}

    with patch("httpx.post", return_value=mock_resp):
        res = parser._call_llm("test prompt")
        assert ".main-image" in res


def test_llm_gateway_gemini_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "dummy_gemini_key")
    parser = SelfHealingDOMParser(db_path=str(tmp_path / "test.db"), llm_provider="gemini")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": '{"selector": "article img", "attribute": "data-src"}'}]}}]
    }

    with patch("httpx.post", return_value=mock_resp):
        res = parser._call_llm("test prompt")
        assert "article img" in res


def test_llm_gateway_openai_mock(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_openai_key")
    parser = SelfHealingDOMParser(db_path=str(tmp_path / "test.db"), llm_provider="openai")

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": '{"selector": "figure > img", "attribute": "src"}'}}]
    }

    with patch("httpx.post", return_value=mock_resp):
        res = parser._call_llm("test prompt")
        assert "figure > img" in res
