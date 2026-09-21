import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from network.session import SessionManager
from storage.analytics_exporter import export_analytics
from frontend.app import app

client = TestClient(app)


class TestSessionDomainCollisionAndTraversal:
    """Adversarial validation for session domain collision and path traversal."""

    def test_session_adversarial_domain_uniqueness(self):
        """Verify that closely-named domains produce distinct filenames with zero collision."""
        sm = SessionManager()

        domain_pairs = [
            ("a.b.com", "a_b.com"),
            ("evil.com", "evil-com"),
            ("test.domain.com", "test_domain_com"),
            ("sub.target.org", "sub-target.org"),
        ]

        for d1, d2 in domain_pairs:
            f1 = sm.get_session_file(d1)
            f2 = sm.get_session_file(d2)
            assert f1 != f2, f"Domain collision detected between {d1} and {d2} -> {f1}"
            assert Path(f1).name != Path(f2).name

    def test_session_cross_domain_cookie_isolation(self, tmp_path, monkeypatch):
        """Verify cookies saved for one domain are never overwritten or read by a collision-candidate domain."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr("network.session.SESSION_DIR", str(session_dir))

        sm = SessionManager()
        d1 = "target.site.com"
        d2 = "target_site_com"

        cookies_d1 = [{"name": "auth_d1", "value": "secret_token_1"}]
        cookies_d2 = [{"name": "auth_d2", "value": "secret_token_2"}]

        sm.save_session(d1, cookies_d1)
        sm.save_session(d2, cookies_d2)

        loaded_d1 = sm.load_session(d1)
        loaded_d2 = sm.load_session(d2)

        assert loaded_d1 == cookies_d1
        assert loaded_d2 == cookies_d2
        assert loaded_d1 != loaded_d2

        sm.evict_session(d1)
        assert sm.load_session(d1) is None
        assert sm.load_session(d2) == cookies_d2  # d2 still intact

    def test_session_path_traversal_rejection(self, tmp_path, monkeypatch):
        """Verify traversal attempts are strictly contained within session directory."""
        session_dir = tmp_path / "sessions"
        session_dir.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr("network.session.SESSION_DIR", str(session_dir))

        sm = SessionManager()
        traversal_domains = [
            "../../etc/passwd",
            "..\\..\\windows\\system32",
            "/absolute/root/domain.com",
            "....//....//escape.com",
        ]

        for bad_domain in traversal_domains:
            session_file = sm.get_session_file(bad_domain)
            # Must remain strictly inside session_dir
            assert Path(session_file).parent == session_dir.resolve()
            assert not str(session_file).startswith(str(session_dir) + "_sibling")


class TestDatasetExportAdversarialTraversal:
    """Verify dataset export endpoint rejects directory traversal and invalid paths."""

    def test_dataset_export_traversal_rejected(self):
        traversal_subjects = [
            "..",
            "../etc",
            "..\\windows",
            "foo/../../bar",
            "subject/subpath",
        ]
        for sub in traversal_subjects:
            res = client.post(f"/api/dataset/export-db/{sub}", json={"format": "json"})
            assert res.status_code in (400, 404, 405), f"Traversal '{sub}' was not rejected: {res.status_code}"


class TestGalleryOpenFolderAdversarialTraversal:
    """Verify gallery open-folder HTMX endpoint rejects path traversal and sibling prefixes."""

    def test_gallery_open_folder_traversal_payloads(self):
        bad_paths = [
            "../../etc",
            "..\\..\\windows",
            "/etc/passwd",
            "C:\\Windows\\System32",
            "valid_folder/../../../escape",
            "../sibling_output",
        ]
        for p in bad_paths:
            res = client.post("/htmx/open-folder", data={"path": p})
            assert res.status_code == 200
            assert res.text in ("Invalid path", "Failed to open"), f"Path '{p}' did not fail safely: {res.text}"


class TestAnalyticsExporterBoundaryHardening:
    """Verify analytics exporter strictly enforces safe boundaries."""

    def test_export_analytics_rejects_arbitrary_system_paths(self):
        outside_dir = Path("C:/completely_outside_system_boundary_12345") if os.name == "nt" else Path("/opt/forbidden_system_boundary_12345")

        with pytest.raises(ValueError, match="escapes allowed workspace boundaries"):
            export_analytics(outside_dir, "csv")
