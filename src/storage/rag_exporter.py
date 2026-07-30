import json
import re
from pathlib import Path
from typing import Any
from monitoring.logger import get_logger

LOGGER = get_logger(__name__)


class RagExporter:
    """Exports scraped page text and metadata into chunked vector embedding payloads (rag_payload.jsonl)."""

    def __init__(
        self,
        output_dir: Path | str = "output",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = self.output_dir / "rag_payload.jsonl"
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> list[str]:
        """Split text into chunks using hybrid section boundaries and sliding window fallback."""
        cleaned_text = re.sub(r"\s+", " ", text).strip()
        if not cleaned_text:
            return []

        if len(cleaned_text) <= self.chunk_size:
            return [cleaned_text]

        # 1. Attempt section splitting on paragraphs / double newlines or punctuation
        sections = re.split(r"(?<=[.!?])\s+", cleaned_text)
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for sec in sections:
            sec_len = len(sec)
            if current_len + sec_len <= self.chunk_size:
                current_chunk.append(sec)
                current_len += sec_len + 1
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [sec]
                current_len = sec_len

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        # 2. Sliding window fallback for over-long chunks
        final_chunks: list[str] = []
        for chunk in chunks:
            if len(chunk) <= self.chunk_size:
                final_chunks.append(chunk)
            else:
                start = 0
                while start < len(chunk):
                    end = start + self.chunk_size
                    final_chunks.append(chunk[start:end])
                    start += self.chunk_size - self.chunk_overlap

        return final_chunks

    def export_page(
        self,
        page_url: str,
        page_title: str,
        text_content: str,
        metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Chunk text content and append vector document entries to rag_payload.jsonl."""
        metadata = metadata or {}
        chunks = self.chunk_text(text_content)
        entries: list[dict[str, Any]] = []

        for idx, chunk in enumerate(chunks):
            entry = {
                "chunk_id": f"{hash(page_url) & 0xFFFFFFFF:08x}_{idx}",
                "chunk_index": idx,
                "total_chunks": len(chunks),
                "source_url": page_url,
                "page_title": page_title,
                "text_chunk": chunk,
                "chunk_size": len(chunk),
                "metadata": metadata,
            }
            entries.append(entry)

        try:
            with open(self.jsonl_path, "a", encoding="utf-8") as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as exc:
            LOGGER.error("Failed to append entries to rag_payload.jsonl: %s", exc)

        return entries
