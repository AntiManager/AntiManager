"""Normalize a UTF-8 file's line endings to CRLF (byte-safe).

Usage: python -X utf8 to_crlf.py <file> [<file> ...]

Only touches CR/LF bytes; no characters are re-decoded or re-encoded, so
Cyrillic content is preserved exactly.
"""
import sys


def to_crlf(path: str) -> None:
    with open(path, "rb") as f:
        raw = f.read()
    normalized = raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n").replace(b"\n", b"\r\n")
    if normalized != raw:
        with open(path, "wb") as f:
            f.write(normalized)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    for p in sys.argv[1:]:
        to_crlf(p)
        print(f"CRLF: {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
