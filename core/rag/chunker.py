"""
core/rag/chunker.py

Document chunker for the GAIA-OS RAG pipeline.
Supports: markdown (.md), plain text (.txt), JSON (.json).
Produces overlapping chunks with full provenance metadata.

Chunk schema:
    text: str               — the chunk text
    source: str             — absolute file path
    doc_title: str          — first H1 heading or filename
    section: str            — nearest H2/H3 heading above the chunk
    chunk_index: int        — position within document
    char_start: int         — character offset in original document
    chunk_id: str           — deterministic hash ID
"""
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


DEFAULT_CHUNK_SIZE = 512
DEFAULT_OVERLAP = 64
SUPPORTED_EXTENSIONS = {".md", ".txt", ".json"}


@dataclass
class Chunk:
    text: str
    source: str
    doc_title: str
    section: str
    chunk_index: int
    char_start: int
    chunk_id: str = field(init=False)

    def __post_init__(self):
        digest = hashlib.sha256(
            f"{self.source}:{self.chunk_index}:{self.text}".encode()
        ).hexdigest()[:16]
        self.chunk_id = f"chunk_{digest}"

    def provenance(self) -> dict:
        return {
            "chunk_id": self.chunk_id,
            "source": self.source,
            "doc_title": self.doc_title,
            "section": self.section,
            "chunk_index": self.chunk_index,
            "char_start": self.char_start,
        }


def _extract_title(text: str, filename: str) -> str:
    match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else Path(filename).stem


def _extract_section(text: str, char_pos: int) -> str:
    """Find the nearest H2/H3 heading at or before char_pos."""
    segment = text[:char_pos]
    matches = list(re.finditer(r"^#{2,3}\s+(.+)$", segment, re.MULTILINE))
    if matches:
        return matches[-1].group(1).strip()
    return "intro"


def _read_file(path: Path) -> str:
    if path.suffix == ".json":
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return json.dumps(data, indent=2)
        except Exception:
            return path.read_text(encoding="utf-8", errors="replace")
    return path.read_text(encoding="utf-8", errors="replace")


def chunk_text(
    text: str,
    source: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> List[Chunk]:
    """Split a string into overlapping chunks."""
    title = _extract_title(text, source)
    chunks = []
    start = 0
    idx = 0
    length = len(text)

    while start < length:
        end = min(start + chunk_size, length)
        chunk_text_str = text[start:end].strip()
        if chunk_text_str:
            section = _extract_section(text, start)
            chunks.append(
                Chunk(
                    text=chunk_text_str,
                    source=source,
                    doc_title=title,
                    section=section,
                    chunk_index=idx,
                    char_start=start,
                )
            )
            idx += 1
        start += chunk_size - overlap

    return chunks


def chunk_file(
    path: Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
) -> List[Chunk]:
    """Read a file and return its chunks."""
    if path.suffix not in SUPPORTED_EXTENSIONS:
        return []
    text = _read_file(path)
    return chunk_text(text, str(path.resolve()), chunk_size, overlap)


def chunk_directory(
    directory: Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    recursive: bool = True,
) -> List[Chunk]:
    """Recursively chunk all supported files in a directory."""
    chunks = []
    glob = directory.rglob("*") if recursive else directory.glob("*")
    for path in sorted(glob):
        if path.is_file() and path.suffix in SUPPORTED_EXTENSIONS:
            chunks.extend(chunk_file(path, chunk_size, overlap))
    return chunks
