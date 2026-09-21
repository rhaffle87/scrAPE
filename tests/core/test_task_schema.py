"""
test_task_schema.py — Adversarial fuzz and boundary tests for distributed task schemas.

Directly verifies AC1.3:
  - Fuzz corpus of path traversal payloads in all filesystem fields.
  - SSRF endpoints (cloud metadata, loopback, link-local, private subnets).
  - Protocol injections (file://, gopher://, ftp://).
  - Out-of-bounds parameters, null bytes, and malformed hash digests.
"""

import pytest
from pydantic import ValidationError
from core.task_schema import CrawlTaskPayload, DownloadTaskPayload, parse_task_payload


PATH_TRAVERSAL_FUZZ_CORPUS = [
    "../../etc/passwd",
    "..\\..\\windows\\system32\\cmd.exe",
    "/etc/shadow",
    "\\windows\\system32",
    "C:\\Windows\\System32",
    "D:\\secrets\\passwords.txt",
    "output/../../../root/.ssh/id_rsa",
    "output\\..\\..\\..\\evil",
    "....//....//....//etc/passwd",
    "..%2f..%2f..%2fetc%2fpasswd",
    "..%5c..%5cwindows",
    "output/\x00/evil",
    "output/test/../../../../boot.ini",
    "../sibling_dir",
    "..\\sibling_dir",
    "./../../escaped",
    "/var/log/messages",
    "\\\\attacker_smb\\share\\evil",
    "output/..;/..;/",
]

SSRF_FUZZ_CORPUS = [
    "http://169.254.169.254/latest/meta-data/",
    "http://169.254.169.254/latest/api/token",
    "http://127.0.0.1:8080/admin",
    "http://127.0.0.1:6379/",
    "http://localhost:3000/api/keys",
    "http://0.0.0.0:8000/",
    "http://[::1]:8080/",
    "http://metadata.google.internal/computeMetadata/v1/",
    "http://metadata.azure.com/metadata/instance",
    "http://instance-data/latest/meta-data/",
    "http://10.0.0.1/internal",
    "http://172.16.0.1/admin",
    "http://192.168.1.1/router",
    "file:///etc/passwd",
    "file:///C:/Windows/win.ini",
    "gopher://127.0.0.1:6379/_FLUSHALL",
    "ftp://internal.vault/secret",
    "javascript:alert(1)",
    "data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==",
    "http://2130706433/",  # Decimal representation of 127.0.0.1
    "http://017700000001/",  # Octal representation of 127.0.0.1
]


def test_crawl_task_valid_payload():
    """Verify happy-path crawl task creation and parsing."""
    raw = {
        "task_id": "crawl_abc_123",
        "task_type": "crawl",
        "seed_url": "https://example.com/gallery",
        "output_dir": "output/crawls",
        "page_limit": 50,
        "depth_limit": 3,
        "domain_whitelist": ["example.com", "cdn.example.com"],
        "lease_ttl": 60,
    }
    task = parse_task_payload(raw)
    assert isinstance(task, CrawlTaskPayload)
    assert task.task_id == "crawl_abc_123"
    assert task.seed_url == "https://example.com/gallery"
    assert task.page_limit == 50
    assert task.domain_whitelist == ["example.com", "cdn.example.com"]


def test_download_task_valid_payload():
    """Verify happy-path download task creation and parsing."""
    raw = {
        "task_id": "dl_999",
        "task_type": "download",
        "media_url": "https://cdn.example.com/images/photo.jpg",
        "destination_path": "output/downloads/photo.jpg",
        "sha256_hint": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "lease_ttl": 45,
    }
    task = parse_task_payload(raw)
    assert isinstance(task, DownloadTaskPayload)
    assert task.task_id == "dl_999"
    assert task.sha256_hint == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


@pytest.mark.parametrize("payload", PATH_TRAVERSAL_FUZZ_CORPUS)
def test_crawl_task_rejects_path_traversal_fuzz(payload):
    """AC1.3: Assert output_dir rejects 100% of path traversal payloads."""
    with pytest.raises((ValidationError, ValueError)):
        CrawlTaskPayload(
            task_id="task_traversal_test",
            seed_url="https://example.com",
            output_dir=payload,
        )


@pytest.mark.parametrize("payload", PATH_TRAVERSAL_FUZZ_CORPUS)
def test_download_task_rejects_path_traversal_fuzz(payload):
    """AC1.3: Assert destination_path rejects 100% of path traversal payloads."""
    with pytest.raises((ValidationError, ValueError)):
        DownloadTaskPayload(
            task_id="task_dl_traversal",
            media_url="https://example.com/img.png",
            destination_path=payload,
        )


@pytest.mark.parametrize("payload", SSRF_FUZZ_CORPUS)
def test_crawl_task_rejects_ssrf_fuzz(payload):
    """AC1.3: Assert seed_url rejects 100% of SSRF and metadata endpoints."""
    with pytest.raises((ValidationError, ValueError)):
        CrawlTaskPayload(
            task_id="task_ssrf_test",
            seed_url=payload,
            output_dir="output",
        )


@pytest.mark.parametrize("payload", SSRF_FUZZ_CORPUS)
def test_download_task_rejects_ssrf_fuzz(payload):
    """AC1.3: Assert media_url rejects 100% of SSRF and metadata endpoints."""
    with pytest.raises((ValidationError, ValueError)):
        DownloadTaskPayload(
            task_id="task_ssrf_test",
            media_url=payload,
            destination_path="output/safe.png",
        )


def test_task_id_injection_rejection():
    """Assert task_id strictly rejects path characters, traversal tokens, and control bytes."""
    malicious_ids = [
        "../../etc/passwd",
        "task/with/slashes",
        "task\\with\\backslashes",
        "task\x00nullbyte",
        "task;rm -rf /",
        "task$(whoami)",
        "task`id`",
        "",  # empty
        "a" * 200,  # oversized
    ]
    for bad_id in malicious_ids:
        with pytest.raises((ValidationError, ValueError)):
            CrawlTaskPayload(
                task_id=bad_id,
                seed_url="https://example.com",
            )


def test_parameter_boundary_enforcement():
    """Assert out-of-bounds numerical and hash parameters are strictly rejected."""
    # Negative / zero page limit
    with pytest.raises((ValidationError, ValueError)):
        CrawlTaskPayload(task_id="t1", seed_url="https://example.com", page_limit=0)
    with pytest.raises((ValidationError, ValueError)):
        CrawlTaskPayload(task_id="t1", seed_url="https://example.com", page_limit=-10)

    # Oversized page limit
    with pytest.raises((ValidationError, ValueError)):
        CrawlTaskPayload(task_id="t1", seed_url="https://example.com", page_limit=999999)

    # Negative lease TTL
    with pytest.raises((ValidationError, ValueError)):
        CrawlTaskPayload(task_id="t1", seed_url="https://example.com", lease_ttl=2)

    # Malformed SHA256 hint
    with pytest.raises((ValidationError, ValueError)):
        DownloadTaskPayload(
            task_id="t1",
            media_url="https://example.com/a.jpg",
            destination_path="output/a.jpg",
            sha256_hint="not_a_valid_sha256_hash",
        )
    with pytest.raises((ValidationError, ValueError)):
        DownloadTaskPayload(
            task_id="t1",
            media_url="https://example.com/a.jpg",
            destination_path="output/a.jpg",
            sha256_hint="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b85G",  # non-hex 'G'
        )
