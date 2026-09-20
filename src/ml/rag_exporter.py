"""RAG vector payload exporter for chunking scraped text into rag_payload.jsonl."""

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
        import os
        abs_out = os.path.abspath(os.path.normpath(str(output_dir).strip()))
        self.output_dir = Path(abs_out)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.jsonl_path = (self.output_dir / "rag_payload.jsonl").resolve()
        out_resolved = self.output_dir.resolve()
        if not str(self.jsonl_path).startswith(str(out_resolved) + os.sep) and self.jsonl_path.parent != out_resolved:
            raise ValueError("Security violation: jsonl_path traverses outside allowed output_dir")
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


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Export RAG text chunks to rag_payload.jsonl.")
    parser.add_argument("--input-dir", required=True, type=str, help="Directory containing files or results to ingest.")
    parser.add_argument("--output-dir", required=False, type=str, default=None, help="Destination directory for rag_payload.jsonl.")
    parser.add_argument("--chunk-size", type=int, default=500, help="Target chunk size in characters.")
    parser.add_argument("--chunk-overlap", type=int, default=50, help="Overlap between chunks in characters.")
    args = parser.parse_args()

    in_dir = Path(args.input_dir)
    out_dir = Path(args.output_dir) if args.output_dir else in_dir
    exporter = RagExporter(output_dir=out_dir, chunk_size=args.chunk_size, chunk_overlap=args.chunk_overlap)

    processed = 0
    results_json = in_dir / "results.json"
    if results_json.exists():
        try:
            with open(results_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            pages = data.get("scanned_pages", [])
            for p in pages:
                url = p if isinstance(p, str) else p.get("url", "")
                exporter.export_page(page_url=url, page_title=in_dir.name, text_content=f"Scraped page from {url} for {in_dir.name}")
                processed += 1
        except Exception as err:
            LOGGER.warning("Could not parse %s: %s", results_json, err)

    for txt_file in in_dir.glob("**/*.txt"):
        if txt_file.name == "rag_payload.jsonl":
            continue
        try:
            content = txt_file.read_text(encoding="utf-8", errors="ignore")
            if content.strip():
                exporter.export_page(page_url=str(txt_file), page_title=txt_file.stem, text_content=content)
                processed += 1
        except Exception:
            pass

    LOGGER.info("RAG Ingestion complete: %d items processed into %s", processed, exporter.jsonl_path)
    print(f"RAG Ingestion complete: {processed} items processed into {exporter.jsonl_path}")

