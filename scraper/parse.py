"""Turns the result page HTML into the rows of the two model CSV files.

Layout assumed (from the screenshots):
  * a summary table  : माननीय न्यायाधीश | पेशी | फैसला | आदेश | स्थगित
  * per judge        : "इजलाश N" text + red judge heading + a table whose header contains 'मुद्दा न.'
The parser does not depend on CSS classes or ids - only on header texts - so it survives cosmetic changes.
"""
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Comment

from . import bsdate
from .config import DATE_STYLE

CAUSE_HEADERS = ["इजलाश नं.", "माननीय जिल्ला न्यायाधीश\xa0", "क्र. स.", "मुद्दा न.", "संकेत नं.",
                 "दर्ता मिति", "मुद्दा विषय", "वादी", "प्रतिवादी", "फाँटबाला", "प्राथमिकता",
                 "कैफियत", "आदेश फैसलाको किसिम"]
JUDGE_HEADERS = ["मिति:", "माननीय न्यायाधीश", "पेशी", "फैसला", "आदेश", "स्थगित"]

_NUM = "0-9०-९"


def clean(text: str) -> str:
    return " ".join((text or "").split())


def _own_cells(tbl):
    for tr in tbl.find_all("tr"):
        if tr.find_parent("table") is tbl:
            yield tr, tr.find_all(["td", "th"], recursive=False)


def _flat_cell(c) -> str:
    return "" if c.find("table") else clean(c.get_text(" "))


def is_cause_table(tbl) -> bool:
    return any("मुद्दा न" in _flat_cell(c) for _, cells in _own_cells(tbl) for c in cells)


def is_summary_table(tbl) -> bool:
    for _, cells in _own_cells(tbl):
        t = [_flat_cell(c) for c in cells]
        if "स्थगित" in t and "पेशी" in t and "फैसला" in t:
            return True
    return False


@dataclass
class ParseResult:
    causes: list = field(default_factory=list)   # list of 13-column rows
    judges: list = field(default_factory=list)   # list of (name, pesi, faisala, aadesh, sthagit)
    heading_date: str = ""                        # 'YYYY-MM-DD' (ASCII) found in "मिति ... को"


def _norm_date(text: str) -> str:
    return bsdate.to_ascii(text)


def _col_index(headers):
    """Map logical column -> index using header texts (order of tests matters: 'प्रतिवादी' before 'वादी')."""
    idx = {}
    for i, h in enumerate(headers):
        if "क्र" in h and "sn" not in idx and "मुद्दा" not in h:
            idx["sn"] = i
        elif "मुद्दा न" in h:
            idx["case"] = i
        elif "दर्ता" in h:
            idx["reg"] = i
        elif "विषय" in h:
            idx["subject"] = i
        elif "प्रतिवादी" in h:
            idx["defendant"] = i
        elif "वादी" in h:
            idx["plaintiff"] = i
        elif "फाँट" in h or "फाट" in h:
            idx["section"] = i
        elif "प्राथमिकता" in h:
            idx["priority"] = i
        elif "कैफियत" in h:
            idx["remarks"] = i
        elif "आदेश" in h or "फैसला" in h:
            idx["order"] = i
    return idx


_POSITIONAL = dict(sn=0, case=1, reg=2, subject=3, plaintiff=4, defendant=5, section=6,
                   priority=7, remarks=8, order=9)


def _split_case(text: str):
    t = clean(text)
    m = re.match(r"^(.*?)\s*(\([^()]*\))\s*$", t)
    return (m.group(1), m.group(2)) if m else (t, "")


def _order(text: str) -> str:
    # site shows "आदेश >> अन्य"; model file has "आदेश-अन्य"
    return re.sub(r"\s*>>\s*", "-", clean(text))


def _court_and_judge(tbl):
    """Walk backwards from a cause table to find its 'इजलाश N' label and judge heading."""
    court = judge = ""
    for s in tbl.find_all_previous(string=True, limit=80):
        if isinstance(s, Comment) or s.parent.name in ("script", "style"):
            continue
        text = clean(s)
        if not text:
            continue
        owner = s.find_parent("table")
        if owner is not None and (is_cause_table(owner) or is_summary_table(owner)):
            break  # reached the previous data table: no heading for this one
        if not court:
            m = re.search(rf"इजलाश\s*([{_NUM}]+)", text)
            if m:
                court = clean(m.group(0))   # keep the site's own text (e.g. "इजलाश३९" has no space)
        if not judge and text.startswith("माननीय") and "न्यायाधीश" in text:
            judge = text
        if court and judge:
            break
    return court, judge


def parse(html: str) -> ParseResult:
    soup = BeautifulSoup(html, "lxml")
    res = ParseResult()

    m = re.search(rf"मिति\s*([{_NUM}]{{4}}-[{_NUM}]{{2}}-[{_NUM}]{{2}})\s*को", soup.get_text(" "))
    if m:
        res.heading_date = _norm_date(m.group(1))

    for tbl in soup.find_all("table"):
        if is_summary_table(tbl):
            seen_header = False
            for _, cells in _own_cells(tbl):
                t = [_flat_cell(c) for c in cells]
                if "स्थगित" in t:               # header row ("माननीय न्यायाधीश | पेशी | ...")
                    seen_header = True
                    continue
                if seen_header and len(t) >= 5 and "न्यायाधीश" in t[0]:
                    res.judges.append(tuple(t[:5]))
        elif is_cause_table(tbl):
            court, judge = _court_and_judge(tbl)
            idx = None
            for _, cells in _own_cells(tbl):
                t = [_flat_cell(c) for c in cells]
                if idx is None:
                    if any("मुद्दा न" in x for x in t):
                        idx = _col_index(t)
                        for k, v in _POSITIONAL.items():   # fill anything the header matching missed
                            idx.setdefault(k, v)
                    continue
                if len(t) < 9 or not any(t):
                    continue
                g = lambda k: t[idx[k]] if idx[k] < len(t) else ""
                case, sig = _split_case(g("case"))
                reg = g("reg")
                if DATE_STYLE == "model":
                    reg = bsdate.site_date_to_model(reg)
                res.causes.append([court, judge, g("sn"), case, sig, reg, g("subject"), g("plaintiff"),
                                   g("defendant"), g("section"), g("priority"), g("remarks"),
                                   _order(g("order"))])
    return res
