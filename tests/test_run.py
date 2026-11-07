import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).parent))
import types
from scraper import bsdate, run, writer, browser, config
import test_roundtrip as T


class FakeSite:
    def __enter__(self): return self
    def __exit__(self, *a): pass
    def open(self): pass
    def search(self, iso):
        return T.build_html() if iso == "2083-07-19" else "<html><body><form></form>no list</body></html>"


def test_range_skip_and_nodata(tmp_path, monkeypatch):
    for m in (writer, run, config):
        monkeypatch.setattr(m, "DATA_DIR", tmp_path / "data", raising=False)
    monkeypatch.setattr(run, "STATE_DIR", tmp_path / "state")
    monkeypatch.setattr(browser, "Site", FakeSite)
    monkeypatch.setattr(run, "DELAY_BETWEEN_DATES", 0)
    dates = list(bsdate.daterange(bsdate.parse_bs("2083-07-18"), bsdate.parse_bs("2083-07-19")))
    s = run.scrape_dates(dates)
    assert s["saved"] == 1 and s["nodata"] == 1
    assert (tmp_path / "data/2083/2083-07-19_Daily_Cause_List_KDC.csv").exists()
    assert (tmp_path / "data/2083/2083-07-19_Daily_Judges_List_KDC_.csv").exists()
    assert not (tmp_path / "data/2083/2083-07-18_Daily_Cause_List_KDC.csv").exists()
    s2 = run.scrape_dates(dates)                     # second run: everything skipped
    assert s2["skipped"] == 2


def test_fallback_to_other_date_is_nodata(tmp_path, monkeypatch):
    for m in (writer, run, config):
        monkeypatch.setattr(m, "DATA_DIR", tmp_path / "data", raising=False)
    monkeypatch.setattr(run, "STATE_DIR", tmp_path / "state")

    class Fallback(FakeSite):
        def search(self, iso):
            return T.build_html()          # always the 2083-07-19 list, whatever date is asked

    monkeypatch.setattr(browser, "Site", Fallback)
    monkeypatch.setattr(run, "DELAY_BETWEEN_DATES", 0)
    d = bsdate.parse_bs("2083-07-21")
    s = run.scrape_dates([d])
    assert s["nodata"] == 1 and s["failed"] == 0
    assert not list((tmp_path / "data").glob("**/*.csv"))
