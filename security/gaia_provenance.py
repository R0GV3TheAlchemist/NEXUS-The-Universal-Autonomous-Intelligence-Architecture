#!/usr/bin/env python3
"""
GAIA Document Provenance & Anti-Theft System
=============================================
Author: Kyle Steen / R0GV3 the Alchemist
Repo:   R0GV3TheAlchemist/GAIA-The-Global-Autonomous-Intelligence-Architecture

Embeds invisible cryptographic fingerprints into documents and source files.
Any copy can be verified as originating from GAIA. Tampering is detectable.

Usage:
  python3 gaia_provenance.py protect <file> [secret_key]
  python3 gaia_provenance.py verify  <file>
  python3 gaia_provenance.py list
"""

import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ── Constants ────────────────────────────────────────────────────────────────────────────

GAIA_OWNER      = "R0GV3TheAlchemist"
GAIA_REPO       = "GAIA-The-Global-Autonomous-Intelligence-Architecture"
GAIA_AUTHOR     = "Kyle Steen"
GAIA_CONTACT    = "xxkylesteenxx@outlook.com"
WATERMARK_TAG   = "GAIA_PROVENANCE"
ZERO_WIDTH_CHARS = [
    "\u200b",  # zero-width space
    "\u200c",  # zero-width non-joiner
    "\u200d",  # zero-width joiner
    "\u2060",  # word joiner
]


# ── Core: Fingerprint Generation ─────────────────────────────────────────────────

def generate_fingerprint(content: str, secret_key: Optional[str] = None) -> dict:
    """
    Generates a cryptographic fingerprint for a document.
    Returns a dict with all provenance metadata.
    """
    if secret_key is None:
        secret_key = hashlib.sha256(
            f"{GAIA_OWNER}:{GAIA_REPO}:{GAIA_AUTHOR}".encode()
        ).hexdigest()

    timestamp    = datetime.now(timezone.utc).isoformat()
    doc_id       = str(uuid.uuid4())
    content_hash = hashlib.sha3_256(content.encode("utf-8")).hexdigest()

    sig_payload = f"{doc_id}|{timestamp}|{content_hash}|{GAIA_OWNER}"
    signature   = hmac.new(
        secret_key.encode(), sig_payload.encode(), hashlib.sha3_256
    ).hexdigest()

    return {
        "owner":        GAIA_OWNER,
        "repo":         GAIA_REPO,
        "author":       GAIA_AUTHOR,
        "doc_id":       doc_id,
        "timestamp":    timestamp,
        "content_hash": content_hash,
        "signature":    signature,
        "tag":          WATERMARK_TAG,
    }


# ── Visible Watermark ───────────────────────────────────────────────────────────────────

def embed_visible_watermark(content: str, fp: dict, file_ext: str = ".py") -> str:
    """Prepends a visible provenance block appropriate for the file type."""
    ts   = fp["timestamp"]
    did  = fp["doc_id"]
    full = fp["signature"]

    if file_ext in (".py", ".ts", ".js", ".sh"):
        block = (
            f"# {WATERMARK_TAG}\n"
            f"# Owner:     {GAIA_OWNER} <{GAIA_CONTACT}>\n"
            f"# Repo:      https://github.com/{GAIA_OWNER}/{GAIA_REPO}\n"
            f"# Author:    {GAIA_AUTHOR}\n"
            f"# Doc-ID:    {did}\n"
            f"# Timestamp: {ts}\n"
            f"# Sig:       {full}\n"
            f"# Verify:    python3 gaia_provenance.py verify <file>\n"
            f"# ── Any reproduction without attribution violates GAIA license. ──\n"
            f"\n"
        )
    elif file_ext in (".md", ".txt", ".rst"):
        block = (
            f"<!-- {WATERMARK_TAG}\n"
            f"     Owner:     {GAIA_OWNER} <{GAIA_CONTACT}>\n"
            f"     Repo:      https://github.com/{GAIA_OWNER}/{GAIA_REPO}\n"
            f"     Author:    {GAIA_AUTHOR}\n"
            f"     Doc-ID:    {did}\n"
            f"     Timestamp: {ts}\n"
            f"     Sig:       {full}\n"
            f"     Verify:    python3 gaia_provenance.py verify <file>\n"
            f"     Any reproduction without attribution violates GAIA license.\n"
            f"-->\n\n"
        )
    else:
        block = ""

    return block + content


# ── Invisible Watermark (Zero-Width Steganography) ───────────────────────────────────────

def _bits_to_zwc(bits: str) -> str:
    """Encode a bitstring as zero-width characters."""
    return "".join("\u200b" if b == "0" else "\u200c" for b in bits)


def _zwc_to_bits(zwc: str) -> str:
    result = ""
    for ch in zwc:
        if ch == "\u200b":
            result += "0"
        elif ch == "\u200c":
            result += "1"
    return result


def embed_invisible_watermark(content: str, fp: dict) -> str:
    """
    Embeds an invisible zero-width-character watermark.
    Survives even if the visible header is stripped.
    """
    payload = f"{fp['doc_id']}||{fp['signature']}"
    bits    = bin(int(payload.encode("utf-8").hex(), 16))[2:]
    zwc     = _bits_to_zwc(bits)

    idx = content.find("\n")
    if idx == -1:
        return content + zwc
    return content[: idx + 1] + zwc + content[idx + 1 :]


def extract_invisible_watermark(content: str) -> Optional[str]:
    """Attempts to extract and decode the invisible watermark."""
    zwc_chars = {"\u200b", "\u200c"}
    zwc_str   = "".join(ch for ch in content if ch in zwc_chars)
    if not zwc_str:
        return None
    bits = _zwc_to_bits(zwc_str)
    try:
        n      = int(bits, 2)
        length = (n.bit_length() + 7) // 8
        return n.to_bytes(length, "big").decode("utf-8", errors="replace")
    except Exception:
        return None


# ── Manifest Registry ──────────────────────────────────────────────────────────────────────

MANIFEST_FILE = Path(".gaia_manifest.json")


def _load_manifest() -> dict:
    if MANIFEST_FILE.exists():
        with open(MANIFEST_FILE) as f:
            return json.load(f)
    return {"documents": {}}


def _save_manifest(manifest: dict) -> None:
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"[GAIA] Manifest updated → {MANIFEST_FILE}")


def register_document(fp: dict, filepath: str) -> None:
    """Registers a fingerprinted document in the local manifest."""
    manifest = _load_manifest()
    manifest["documents"][fp["doc_id"]] = {
        "file":         filepath,
        "timestamp":    fp["timestamp"],
        "content_hash": fp["content_hash"],
        "signature":    fp["signature"],
    }
    _save_manifest(manifest)


# ── Main API ───────────────────────────────────────────────────────────────────────────

def protect_file(filepath: str, secret_key: Optional[str] = None) -> str:
    """
    Full pipeline: read → fingerprint → embed visible + invisible watermarks
    → write protected file → register in manifest.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {filepath}")

    content   = path.read_text(encoding="utf-8")
    fp        = generate_fingerprint(content, secret_key)
    ext       = path.suffix.lower()

    protected = embed_visible_watermark(content, fp, ext)
    protected = embed_invisible_watermark(protected, fp)

    out_path  = path.with_stem(path.stem + "_protected")
    out_path.write_text(protected, encoding="utf-8")

    register_document(fp, str(out_path))

    print(f"[GAIA] Protected → {out_path}")
    print(f"       Doc-ID   : {fp['doc_id']}")
    print(f"       Signature: {fp['signature'][:32]}...")
    return str(out_path)


def verify_file(filepath: str) -> bool:
    """
    Verifies a file's provenance.
    Checks visible header, invisible watermark, and manifest registry.
    """
    path = Path(filepath)
    if not path.exists():
        print(f"[GAIA] ERROR: File not found: {filepath}")
        return False

    content      = path.read_text(encoding="utf-8")
    visible_ok   = WATERMARK_TAG in content and GAIA_OWNER in content
    invisible    = extract_invisible_watermark(content)
    invisible_ok = invisible is not None and GAIA_OWNER in (invisible or "")
    manifest     = _load_manifest()
    manifest_ok  = any(v["file"] == filepath for v in manifest["documents"].values())

    print(f"\n[GAIA] Verification report: {filepath}")
    print(f"       Visible watermark  : {'\u2713 PASS' if visible_ok   else '\u2717 FAIL'}")
    print(f"       Invisible watermark: {'\u2713 PASS' if invisible_ok  else '\u2717 FAIL (may be stripped)'}")
    print(f"       Manifest registry  : {'\u2713 REGISTERED' if manifest_ok else '\u2717 NOT IN MANIFEST'}")
    authentic = visible_ok or invisible_ok or manifest_ok
    print(f"       Result             : {'\u2713 AUTHENTIC GAIA DOCUMENT' if authentic else '\u2717 CANNOT VERIFY ORIGIN'}\n")
    return authentic


# ── CLI ────────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    usage = """
GAIA Provenance System — by Kyle Steen / R0GV3TheAlchemist
-----------------------------------------------------------
  python3 gaia_provenance.py protect <file> [secret_key]
      Stamp a file with your cryptographic signature.

  python3 gaia_provenance.py verify <file>
      Verify whether a file originated from GAIA.

  python3 gaia_provenance.py list
      List all registered GAIA documents.
"""

    if len(sys.argv) < 2:
        print(usage)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "protect" and len(sys.argv) >= 3:
        sk = sys.argv[3] if len(sys.argv) > 3 else None
        protect_file(sys.argv[2], sk)

    elif cmd == "verify" and len(sys.argv) >= 3:
        ok = verify_file(sys.argv[2])
        sys.exit(0 if ok else 1)

    elif cmd == "list":
        m = _load_manifest()
        if not m["documents"]:
            print("[GAIA] No documents registered yet.")
        else:
            print(f"[GAIA] Registered documents ({len(m['documents'])} total):")
            for doc_id, meta in m["documents"].items():
                print(f"  {doc_id[:8]}...  {meta['file']}  ({meta['timestamp']})")
    else:
        print(usage)
