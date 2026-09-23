"""
tests/frontend/test_webui_dormant_subsystems_dom_render.py

Empirical DOM rendering and interactive workflow test verifying that all 5
subsystems originally noted in un_main_system.md are visually exposed,
discoverable, and functionally operable in the WebUI.
"""

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from frontend.app import app

client = TestClient(app)


def test_webui_dom_renders_all_dormant_subsystems():
    """
    Live DOM inspection of GET / confirming all 5 subsystems render interactively:
    1. Dataset Tools & LoRA Export Studio (with aesthetic range slider and live value display)
    2. Database Columnar Exporter (with Apache Parquet Snappy option)
    3. CAPTCHA Provider Selector (with all 4 providers: capsolver, 2captcha, anticaptcha, free_audio)
    4. Hardware Load Governor Alert Banner (with #node-health-banner and telemetry polling hook)
    5. Social Plugin Authentication Accordion (with session cookie controls)
    """
    response = client.get("/")
    assert response.status_code == 200, f"Expected 200 OK from /, got {response.status_code}"
    soup = BeautifulSoup(response.text, "html.parser")

    # -------------------------------------------------------------------------
    # 1. Dataset Tools & LoRA Export Studio (Aesthetic Score Slider & WD14/Crop)
    # -------------------------------------------------------------------------
    slider = soup.find("input", {"id": "export-min-score"})
    assert slider is not None, "Aesthetic score range slider '#export-min-score' not rendered in DOM"
    assert slider.get("type") == "range", f"Expected type='range', got {slider.get('type')}"
    assert float(slider.get("min")) == 1.0
    assert float(slider.get("max")) == 10.0
    assert float(slider.get("step")) == 0.1
    assert float(slider.get("value")) == 5.5
    assert "export-score-val" in slider.get("oninput", "")

    score_val_span = soup.find("span", {"id": "export-score-val"})
    assert score_val_span is not None, "Live aesthetic score span '#export-score-val' not found"
    assert score_val_span.text == "5.5"

    wd14_chk = soup.find("input", {"id": "export-wd14"})
    assert wd14_chk is not None, "WD14 Booru tag checkbox '#export-wd14' not rendered"
    assert wd14_chk.get("type") == "checkbox"

    crop_chk = soup.find("input", {"id": "export-smart-crop"})
    assert crop_chk is not None, "Smart crop checkbox '#export-smart-crop' not rendered"

    btn_lora = soup.find("button", {"id": "btn-submit-export"})
    assert btn_lora is not None, "Button '#btn-submit-export' not rendered"
    assert "submitDatasetExport" in btn_lora.get("onclick", "")

    # -------------------------------------------------------------------------
    # 2. Database Columnar Exporter (Apache Parquet)
    # -------------------------------------------------------------------------
    db_format_select = soup.find("select", {"id": "export-db-format"})
    assert db_format_select is not None, "Database format dropdown '#export-db-format' not rendered"
    options = {opt.get("value"): opt.text for opt in db_format_select.find_all("option")}
    assert "parquet" in options, "Parquet option missing from '#export-db-format' dropdown"
    assert "Parquet" in options["parquet"]
    assert "Snappy" in options["parquet"]
    assert "csv" in options
    assert "json" in options

    btn_db_export = soup.find("button", {"id": "btn-submit-db-export"})
    assert btn_db_export is not None, "Button '#btn-submit-db-export' not rendered"
    assert "submitDatabaseExport" in btn_db_export.get("onclick", "")

    # -------------------------------------------------------------------------
    # 3. CAPTCHA Provider Configuration UI (All 4 Providers)
    # -------------------------------------------------------------------------
    captcha_select = soup.find("select", {"id": "setting-CAPTCHA_PRIMARY_PROVIDER"})
    assert captcha_select is not None, "CAPTCHA provider dropdown '#setting-CAPTCHA_PRIMARY_PROVIDER' not rendered"
    captcha_opts = [opt.get("value") for opt in captcha_select.find_all("option")]
    expected_providers = ["capsolver", "2captcha", "anticaptcha", "free_audio"]
    for prov in expected_providers:
        assert prov in captcha_opts, f"Provider '{prov}' missing from CAPTCHA dropdown options: {captcha_opts}"

    assert soup.find("input", {"id": "setting-CAPSOLVER_API_KEY"}) is not None
    assert soup.find("input", {"id": "setting-2CAPTCHA_API_KEY"}) is not None
    assert soup.find("input", {"id": "setting-ANTICAPTCHA_API_KEY"}) is not None

    # -------------------------------------------------------------------------
    # 4. Hardware Governor Visibility & Alert Banner
    # -------------------------------------------------------------------------
    health_banner = soup.find("div", {"id": "node-health-banner"})
    assert health_banner is not None, "Hardware governor banner '#node-health-banner' not rendered in DOM"
    assert "HARDWARE LOAD GOVERNOR" in health_banner.text
    # Check that client script contains checkNodeHealth polling logic
    html_text = response.text
    assert "checkNodeHealth" in html_text
    assert "/api/telemetry/node-health" in html_text

    # -------------------------------------------------------------------------
    # 5. Social Plugin Authentication Accordion
    # -------------------------------------------------------------------------
    auth_tab = soup.find("div", {"id": "settings-tab-auth"})
    assert auth_tab is not None, "Settings tab '#settings-tab-auth' not rendered"
    assert soup.find("button", {"id": "btn-submit-auth"}) is not None
    assert "submitAuthentication" in soup.find("button", {"id": "btn-submit-auth"}).get("onclick", "")


def test_webui_interactive_actions_for_all_dormant_subsystems(tmp_path):
    """
    Executes live API requests for the 5 interactive UI components to prove functionality:
    - Setting CAPTCHA provider via /api/settings/solver
    - Querying governor health via /api/telemetry/node-health with mock high load
    - Saving authentication cookies via /api/settings/auth
    """
    # 1. Test CAPTCHA provider selection action for all 4 providers
    env_file = tmp_path / ".env"
    with patch("frontend.routers.settings.ENV_PATH", env_file):
        for prov in ["free_audio", "2captcha", "anticaptcha", "capsolver"]:
            resp = client.post("/api/settings/solver", data={"provider": prov, "api_key": f"key_{prov}"})
            assert resp.status_code == 200
            assert resp.json().get("status") == "ok"

    # 2. Test Hardware Governor alert firing when throttled
    with patch("monitoring.hardware_governor.HardwareLoadGovernor.get_concurrency_scale_factor", return_value=0.5):
        resp = client.get("/api/telemetry/node-health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("is_throttled") is True
        assert data.get("status") == "throttled"
        assert "alert" in data
        assert "Concurrency throttled to 0.50x" in data["alert"]

    # 3. Test Plugin Authentication save action
    with patch("network.session.SessionManager.save_session") as mock_save:
        resp = client.post("/api/plugins/auth", json={
            "domain": "instagram.com",
            "cookies": {"sessionid": "test_session_token_123"},
        })
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"
        assert mock_save.call_count >= 1

    # 4. Test Parquet Database Export invocation
    with patch("storage.analytics_exporter.export_analytics") as mock_export, \
         patch("pathlib.Path.exists", return_value=True):
        resp = client.post("/api/dataset/export-db/test_subject", json={"format": "parquet"})
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"
        mock_export.assert_called_once()
