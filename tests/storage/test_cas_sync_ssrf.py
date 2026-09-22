"""
tests/storage/test_cas_sync_ssrf.py

Adversarial testing for S3 endpoint SSRF and cloud metadata defense (AC2.2).
Proves that validate_s3_endpoint_url() strictly rejects cloud metadata (169.254.169.254),
internal GCP/Azure metadata hosts, private CIDRs, and loopback addresses,
while permitting legitimate public endpoints and allowing loopback only under explicit override.
"""

import pytest
from common.security import validate_s3_endpoint_url


class TestS3EndpointSSRFDefense:
    """AC2.2: S3_ENDPOINT_URL must block SSRF, cloud metadata, and unauthorized loopback."""

    @pytest.mark.parametrize(
        "metadata_url",
        [
            "http://169.254.169.254/",
            "http://169.254.169.254:80/latest/meta-data/",
            "http://metadata.google.internal/computeMetadata/v1/",
            "http://instance-data/latest/meta-data/",
            "http://metadata.azure.com/metadata/instance",
        ],
    )
    def test_cloud_metadata_always_blocked(self, metadata_url, monkeypatch):
        """Cloud metadata endpoints must be rejected even if local override is active."""
        # Unset override
        monkeypatch.delenv("SCRAPE_ALLOW_LOCAL_S3_ENDPOINT", raising=False)
        with pytest.raises(ValueError, match="SSRF blocked"):
            validate_s3_endpoint_url(metadata_url)

        # Set override — cloud metadata MUST STILL BE BLOCKED!
        monkeypatch.setenv("SCRAPE_ALLOW_LOCAL_S3_ENDPOINT", "true")
        with pytest.raises(ValueError, match="SSRF blocked"):
            validate_s3_endpoint_url(metadata_url)

    @pytest.mark.parametrize(
        "loopback_url",
        [
            "http://127.0.0.1:9000",
            "http://localhost:9000",
            "http://127.0.0.1/",
            "http://[::1]:9000",
        ],
    )
    def test_loopback_blocked_by_default(self, loopback_url, monkeypatch):
        """Loopback endpoints must be blocked by default."""
        monkeypatch.delenv("SCRAPE_ALLOW_LOCAL_S3_ENDPOINT", raising=False)
        with pytest.raises(ValueError, match="SSRF blocked"):
            validate_s3_endpoint_url(loopback_url)

    @pytest.mark.parametrize(
        "loopback_url",
        [
            "http://127.0.0.1:9000",
            "http://localhost:9000",
            "http://127.0.0.1/",
            "http://[::1]:9000",
        ],
    )
    def test_loopback_allowed_under_explicit_override(self, loopback_url, monkeypatch):
        """Loopback endpoints are permitted for MinIO testing only when explicit flag is set."""
        monkeypatch.setenv("SCRAPE_ALLOW_LOCAL_S3_ENDPOINT", "true")
        assert validate_s3_endpoint_url(loopback_url) == loopback_url

    @pytest.mark.parametrize(
        "private_ip_url",
        [
            "http://10.0.0.1:9000",
            "http://192.168.1.50:9000",
            "http://172.16.0.1:9000",
            "http://172.31.255.255:9000",
        ],
    )
    def test_private_ip_ranges_blocked(self, private_ip_url, monkeypatch):
        """Private RFC 1918 CIDR networks must be blocked."""
        monkeypatch.delenv("SCRAPE_ALLOW_LOCAL_S3_ENDPOINT", raising=False)
        with pytest.raises(ValueError, match="SSRF blocked"):
            validate_s3_endpoint_url(private_ip_url)

    @pytest.mark.parametrize(
        "bad_scheme_url",
        [
            "ftp://s3.amazonaws.com",
            "file:///etc/passwd",
            "gopher://127.0.0.1:9000",
            "dict://127.0.0.1:11211",
        ],
    )
    def test_non_http_schemes_blocked(self, bad_scheme_url, monkeypatch):
        """Non-HTTP/HTTPS schemes must be rejected."""
        monkeypatch.delenv("SCRAPE_ALLOW_LOCAL_S3_ENDPOINT", raising=False)
        with pytest.raises(ValueError, match="SSRF blocked"):
            validate_s3_endpoint_url(bad_scheme_url)

    @pytest.mark.parametrize(
        "valid_endpoint",
        [
            "https://s3.amazonaws.com",
            "https://s3.us-west-2.amazonaws.com",
            "https://bucket-name.r2.cloudflarestorage.com",
            "https://storage.googleapis.com",
        ],
    )
    def test_valid_public_endpoints_allowed(self, valid_endpoint, monkeypatch):
        """Valid public cloud storage endpoints must return cleanly."""
        monkeypatch.delenv("SCRAPE_ALLOW_LOCAL_S3_ENDPOINT", raising=False)
        assert validate_s3_endpoint_url(valid_endpoint) == valid_endpoint

    def test_none_or_empty_endpoint_returns_none(self):
        """Empty or None endpoint URLs return None without raising error."""
        assert validate_s3_endpoint_url(None) is None
        assert validate_s3_endpoint_url("") is None
        assert validate_s3_endpoint_url("   ") is None

    def test_ssrf_validation_has_zero_external_dependencies_and_unconditional_execution(self):
        """
        Point 6: Confirm validate_s3_endpoint_url() has zero dependency on boto3, redis, or cloud SDKs.
        The function must execute unconditionally and never be skipped in CI regardless of
        optional dependency availability.
        """
        import sys

        with pytest.MonkeyPatch.context() as mp:
            mp.setitem(sys.modules, "boto3", None)
            mp.setitem(sys.modules, "redis", None)

            # Cloud metadata must be blocked without any cloud SDK installed
            with pytest.raises(ValueError, match="SSRF blocked"):
                validate_s3_endpoint_url("http://169.254.169.254/latest/meta-data/")

            # Public cloud URL must pass
            public_url = "https://s3.us-west-2.amazonaws.com"
            assert validate_s3_endpoint_url(public_url) == public_url

