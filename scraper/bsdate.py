"""Bikram Sambat (Nepali) date helpers."""
import datetime as dt
import re
from zoneinfo import ZoneInfo

import nepali_datetime

_TO_DEV = str.maketrans("0123456789", "०१२३४५६७८९")
_TO_ASCII = str.maketrans("०१२३४५६७८९", "0123456789")


def to_dev(s) -> str:
    return str(s).translate(_TO_DEV)


def to_ascii(s) -> str:
    return str(s).translate(_TO_ASCII)


def parse_bs(s: str):
    y, m, d = (int(x) for x in to_ascii(s).strip().split("-"))
    return nepali_datetime.date(y, m, d)


def iso(d) -> str:
    return f"{d.year:04d}-{d.month:02d}-{d.day:02d}"


def today_bs():
    """Today's BS date in Nepal time (GitHub runners use UTC)."""
    now = dt.datetime.now(ZoneInfo("Asia/Kathmandu")).date()
    return nepali_datetime.date.from_datetime_date(now)


def daterange(start, end):
    d = start
    while d <= end:
        yield d
        d += dt.timedelta(days=1)


def year_end(year: int):
    return nepali_datetime.date(year + 1, 1, 1) - dt.timedelta(days=1)


def site_date_to_model(text: str) -> str:
    """'२०८३-०७-१८' -> '०७/१८/२०८३' (as in the model CSV). Anything else is returned unchanged."""
    m = re.fullmatch(r"\s*([०-९0-9]{4})-([०-९0-9]{1,2})-([०-९0-9]{1,2})\s*", text)
    if not m:
        return text
    y, mo, d = (to_dev(g) for g in m.groups())
    return f"{mo.zfill(2)}/{d.zfill(2)}/{y}"
