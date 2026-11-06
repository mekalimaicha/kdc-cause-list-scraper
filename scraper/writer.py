"""CSV output identical in layout to the two model files (UTF-8 with BOM, CRLF, Excel-style quoting)."""
import csv
import io
from pathlib import Path

from . import bsdate
from .config import (CAUSE_FILE, DATA_DIR, DATE_STYLE, JUDGES_FILE, JUDGES_TRAILING_BLANK_ROW)
from .parse import CAUSE_HEADERS, JUDGE_HEADERS


def _to_bytes(rows) -> bytes:
    buf = io.StringIO(newline="")
    w = csv.writer(buf, lineterminator="\r\n")
    w.writerows(rows)
    return buf.getvalue().encode("utf-8-sig")


def year_dir(iso: str) -> Path:
    return DATA_DIR / iso[:4]


def cause_path(iso: str) -> Path:
    return year_dir(iso) / CAUSE_FILE.format(iso=iso)


def judges_path(iso: str) -> Path:
    return year_dir(iso) / JUDGES_FILE.format(iso=iso)


def _save(path: Path, data: bytes) -> bool:
    """Atomic write. Returns True if the file was created or its content changed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == data:
        return False
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)
    return True


def write_cause(iso: str, rows) -> bool:
    return _save(cause_path(iso), _to_bytes([CAUSE_HEADERS] + rows))


def write_judges(iso: str, judges) -> bool:
    y, m, day = iso.split("-")
    date_cell = f"{bsdate.to_dev(m)}/{bsdate.to_dev(day)}/{bsdate.to_dev(y)}" if DATE_STYLE == "model" \
        else bsdate.to_dev(iso)
    rows = [JUDGE_HEADERS] + [[date_cell, *j] for j in judges]
    if JUDGES_TRAILING_BLANK_ROW:
        rows.append([""] * 6)
    return _save(judges_path(iso), _to_bytes(rows))
