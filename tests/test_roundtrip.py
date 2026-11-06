"""Rebuilds a page shaped like the screenshots from your two model CSVs, runs it through the parser +
writer and requires a byte-identical result. (Dates in M/D/Y form are turned back into the site's Y-M-D.)"""
import csv
import io
import re
import sys
from html import escape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scraper import bsdate, config, parse as P, writer  # noqa: E402

FIX = Path(__file__).parent / "fixtures"
ISO = "2083-07-19"


def rows_of(name):
    return list(csv.reader(io.StringIO((FIX / name).read_bytes().decode("utf-8-sig"), newline="")))


def site_date(v):
    m = re.fullmatch(r"(\d\d)/(\d\d)/(\d{4})", bsdate.to_ascii(v))
    return bsdate.to_dev(f"{m.group(3)}-{m.group(1)}-{m.group(2)}") if m else v


def site_order(v):
    return re.sub(r"^(आदेश|फैसला / अन्तिम आदेश)-", r"\1 >> ", v)


def build_html():
    cause = rows_of("2083-07-19_Daily_Cause_List_KDC.csv")[1:]
    judges = [r for r in rows_of("2083-07-19_Daily_Judges_List_KDC_.csv")[1:] if any(r)]
    h = [f"<html><body><form><input type='text' value='x'><input type='submit' value='खोज्नु होस्'></form>"]
    h.append("<table><tr><th>माननीय न्यायाधीश</th><th>पेशी</th><th>फैसला</th><th>आदेश</th><th>स्थगित</th></tr>")
    for j in judges:
        h.append("<tr>" + "".join(f"<td>{escape(x)}</td>" for x in j[1:]) + "</tr>")
    h.append("</table>")
    h.append(f"<div>मिति {bsdate.to_dev(ISO)} को<br>दैनिक पेशी सूची</div>")
    cur = None
    for r in cause:
        if (r[0], r[1]) != cur:
            if cur:
                h.append("</table>")
            cur = (r[0], r[1])
            h.append(f"<div><span style='float:left'>{escape(r[0])}</span><b>{escape(r[1])}</b></div>")
            h.append("<table><tr><th>क्र. स.</th><th>मुद्दा न.</th><th>दर्ता मिति</th><th>मुद्दा विषय</th>"
                     "<th>वादी</th><th>प्रतिवादी</th><th>फाँटबाला</th><th>प्राथमिकता</th><th>कैफियत</th>"
                     "<th>आदेश<br>फैसलाको<br>किसिम</th></tr>")
        case = f"{escape(r[3])}<br>{escape(r[4])}"
        cells = [escape(r[2]), case, escape(site_date(r[5])), escape(r[6]), escape(r[7]), escape(r[8]),
                 escape(r[9]).replace(" (", "<br>("), escape(r[10]), escape(r[11]), escape(site_order(r[12]))]
        h.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    h.append("</table></body></html>")
    return "\n".join(h)


def test_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(writer, "DATA_DIR", tmp_path)
    res = P.parse(build_html())
    assert res.heading_date == ISO
    writer.write_cause(ISO, res.causes)
    writer.write_judges(ISO, res.judges)
    out_c = writer.cause_path(ISO).read_bytes()
    out_j = writer.judges_path(ISO).read_bytes()
    # Excel left 2 dates of the model as Y-M-D text (day 31/32 is not a valid Gregorian date) and turned 17 into
    # serial numbers; the scraper writes ALL real dates consistently as M/D/Y, so compare on that basis.
    exp = (FIX / "2083-07-19_Daily_Cause_List_KDC.csv").read_bytes().decode("utf-8-sig")
    exp = re.sub(r"(?<![०-९])(२०\d\d|[०-९]{4})-([०-९]{2})-([०-९]{2})(?![०-९])",
                 lambda m: f"{m.group(2)}/{m.group(3)}/{m.group(1)}", exp).encode("utf-8-sig")
    assert out_c == exp
    assert out_j == (FIX / "2083-07-19_Daily_Judges_List_KDC_.csv").read_bytes()
    assert writer.cause_path(ISO).parent.name == "2083"
    assert writer.cause_path(ISO).name == "2083-07-19_Daily_Cause_List_KDC.csv"
    assert writer.judges_path(ISO).name == "2083-07-19_Daily_Judges_List_KDC_.csv"
