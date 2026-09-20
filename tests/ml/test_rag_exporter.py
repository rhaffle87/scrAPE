import json
import tempfile
from pathlib import Path

from ml.rag_exporter import RagExporter



def test_rag_exporter_chunk_text():
    """Verify chunk_text splits long text into chunks cleanly."""
    exporter = RagExporter(chunk_size=100, chunk_overlap=20)
    sample_text = (
        "scrAPE is a high performance media extraction engine. "
        "It supports multi engine web search providers, stealth WAF bypass pipelines, "
        "and automated dataset curation for machine learning training. "
        "All components follow strict zero border radius brutalist design principles."
    )
    chunks = exporter.chunk_text(sample_text)
    assert len(chunks) >= 2
    assert all(len(c) <= 120 for c in chunks)


def test_rag_exporter_export_page():
    """Verify export_page creates rag_payload.jsonl entries."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        exporter = RagExporter(output_dir=tmp_path, chunk_size=80)

        entries = exporter.export_page(
            page_url="https://example.com/article",
            page_title="Test Article Title",
            text_content="This is sentence one. This is sentence two. This is sentence three.",
            metadata={"domain": "example.com", "depth": 1},
        )

        assert len(entries) >= 1
        assert entries[0]["page_title"] == "Test Article Title"
        assert entries[0]["source_url"] == "https://example.com/article"

        jsonl_path = tmp_path / "rag_payload.jsonl"
        assert jsonl_path.exists()

        lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == len(entries)
        parsed = json.loads(lines[0])
        assert parsed["chunk_index"] == 0
