"""Upload security controls.

Uploaded files are treated as untrusted input:
* only .csv is accepted;
* size is capped (MAX_FILE_SIZE_BYTES);
* the first bytes are sniffed to reject obviously binary payloads;
* content is parsed as data only - never executed or eval'd;
* CSV export cells are escaped against spreadsheet formula injection;
* server filesystem paths are never included in errors or responses.
"""
from __future__ import annotations

from api.errors import FileSecurityError
from config import ALLOWED_UPLOAD_EXTENSIONS, MAX_FILE_SIZE_BYTES

BINARY_SIGNATURES = (b"PK\x03\x04", b"\x7fELF", b"MZ", b"\x89PNG", b"%PDF", b"\xff\xd8\xff", b"GIF8")


def validate_upload(filename: str | None, size: int, head: bytes) -> None:
    if not filename:
        raise FileSecurityError("MISSING_FILENAME", "No file name was provided.")

    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        raise FileSecurityError(
            "UNSUPPORTED_FILE_TYPE",
            "Only CSV files are supported. Please upload a .csv file.",
            {"filename_extension": ext or None},
        )

    if size <= 0:
        raise FileSecurityError("EMPTY_FILE", "The uploaded file is empty.")

    if size > MAX_FILE_SIZE_BYTES:
        raise FileSecurityError(
            "FILE_TOO_LARGE",
            f"The uploaded file exceeds the {MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB limit.",
        )

    if head[:8] and any(head.startswith(sig) for sig in BINARY_SIGNATURES):
        raise FileSecurityError(
            "BINARY_CONTENT_DETECTED",
            "The uploaded file does not look like a CSV text file.",
        )


def sanitize_csv_cell(value) -> str:
    """Neutralise spreadsheet formula injection (=, +, -, @ prefixes, tabs, CR)."""
    s = "" if value is None else str(value)
    if s.startswith(("=", "+", "-", "@", "\t", "\r")):
        s = "'" + s
    return s.replace("\r", " ").replace("\n", " ")
