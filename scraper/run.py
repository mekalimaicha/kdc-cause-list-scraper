"""Command line entry point.

  python -m scraper.run range  --start 2072-01-01 --end 2072-12-30 [--force] [--git-push]
  python -m scraper.run daily  [--git-push]
  python -m scraper.run probe  --date 2083-07-18
  python -m scraper.run plan   --start 2072-01-01 --end 2083-07-19      (prints a GitHub matrix as JSON)
"""
import argparse
import datetime as dt
import json
import re
import sys
import time
from pathlib import Path

from . import bsdate, writer
from .config import (DAILY_MAX_LOOKBACK_DAYS, DAILY_START, DATA_DIR, DELAY_BETWEEN_DATES, HISTORICAL_END,
                     HISTORICAL_START, RETRIES, ROOT, STATE_DIR)
from .parse import parse

COMMIT_EVERY = 40


# ------------------------------------------------------------------ state files (one per year => no merge conflicts)
def _state_file(kind: str, year: str) -> Path:
    return STATE_DIR / kind / f"{year}.txt"


def _load(kind: str, year: str) -> set:
    p = _state_file(kind, year)
    return set(p.read_text().split()) if p.exists() else set()


def _save(kind: str, year: str, values: set) -> None:
    p = _state_file(kind, year)
    p.parent.mkdir(parents=True, exist_ok=True)
    if values:
        p.write_text("\n".join(sorted(values)) + "\n")
    elif p.exists():
        p.unlink()


# ------------------------------------------------------------------ core
class StaleResult(Exception):
    pass


def fetch_and_store(site, iso: str):
    """Returns ('data'|'nodata', changed:bool)."""
    html = site.search(iso)
    res = parse(html)
    if (res.causes or res.judges) and res.heading_date and res.heading_date != iso:
        # The site falls back to another day's list when the requested date has none
        # (tomorrow not yet published, holiday...). Confirm once with a fresh page load, then treat as "no list".
        site.open()
        res = parse(site.search(iso))
        if (res.causes or res.judges) and res.heading_date and res.heading_date != iso:
            print(f"[info] {iso}: site shows {res.heading_date} instead -> no list for this date", flush=True)
            return "nodata", False
    changed = False
    if res.causes:
        changed |= writer.write_cause(iso, res.causes)
    if res.judges:
        changed |= writer.write_judges(iso, res.judges)
    return ("data" if (res.causes or res.judges) else "nodata"), changed


def scrape_dates(dates, force=False, refetch=(), git_push=False):
    from .browser import Site
    today = bsdate.today_bs()
    refetch = set(refetch)
    stats = dict(saved=0, updated=0, skipped=0, nodata=0, failed=0)
    since_commit = 0
    nodata = {}
    failed = {}
    todo = []
    for d in dates:
        iso = bsdate.iso(d)
        y = iso[:4]
        nodata.setdefault(y, _load("no_data", y))
        failed.setdefault(y, _load("failed", y))
        both = writer.cause_path(iso).exists() and writer.judges_path(iso).exists()
        if not force and iso not in refetch and (both or iso in nodata[y]):
            stats["skipped"] += 1
            continue
        todo.append(iso)
    print(f"[plan] {len(todo)} dates to fetch, {stats['skipped']} skipped (already done)", flush=True)
    if not todo:
        return stats

    site_cm = Site()
    site = site_cm.__enter__()
    try:
        for n, iso in enumerate(todo, 1):
            y = iso[:4]
            outcome = None
            for attempt in range(1, RETRIES + 1):
                try:
                    kind, changed = fetch_and_store(site, iso)
                    outcome = (kind, changed)
                    break
                except Exception as e:  # network error, stale page, layout problem...
                    print(f"[warn] {iso} attempt {attempt}/{RETRIES}: {e}", flush=True)
                    time.sleep(5 * attempt)
                    try:
                        site.open()
                    except Exception:
                        try:                                # browser may be dead: restart it
                            site_cm.__exit__(None, None, None)
                            site_cm = Site()
                            site = site_cm.__enter__()
                        except Exception as e2:
                            print(f"[warn] restart failed: {e2}", flush=True)
            if outcome is None:
                stats["failed"] += 1
                failed[y].add(iso)
                print(f"[FAIL] {iso}", flush=True)
            else:
                kind, changed = outcome
                failed[y].discard(iso)
                if kind == "data":
                    if changed:
                        stats["updated" if iso in refetch else "saved"] += 1
                    print(f"[{n}/{len(todo)}] {iso} data {'(written)' if changed else '(unchanged)'}", flush=True)
                    nodata[y].discard(iso)
                else:
                    stats["nodata"] += 1
                    print(f"[{n}/{len(todo)}] {iso} no list (holiday / not published)", flush=True)
                    if bsdate.parse_bs(iso) < today:        # today / future may still be published later
                        nodata[y].add(iso)
                since_commit += 1
            if git_push and since_commit >= COMMIT_EVERY:
                _flush_state(nodata, failed)
                from .gitsync import commit_and_push
                commit_and_push(f"Cause lists up to {iso}")
                since_commit = 0
            time.sleep(DELAY_BETWEEN_DATES)
    finally:
        site_cm.__exit__(None, None, None)
        _flush_state(nodata, failed)
        if git_push:
            from .gitsync import commit_and_push
            commit_and_push(f"Cause lists: run finished ({dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC)")
    return stats


def _flush_state(nodata, failed):
    for y, s in nodata.items():
        _save("no_data", y, s)
    for y, s in failed.items():
        _save("failed", y, s)


# ------------------------------------------------------------------ commands
def latest_scraped():
    best = None
    for p in DATA_DIR.glob("*/*_Daily_Cause_List_KDC.csv"):
        m = re.match(r"(\d{4}-\d{2}-\d{2})_", p.name)
        if m and (best is None or m.group(1) > best):
            best = m.group(1)
    return bsdate.parse_bs(best) if best else None


def cmd_daily(a):
    today = bsdate.today_bs()
    tomorrow = today + dt.timedelta(days=1)
    start = bsdate.parse_bs(DAILY_START)
    last = latest_scraped()
    if last and last + dt.timedelta(days=1) > start:
        start = last + dt.timedelta(days=1)
    start = max(start, today - dt.timedelta(days=DAILY_MAX_LOOKBACK_DAYS))
    start = min(start, today)
    refetch = {bsdate.iso(today), bsdate.iso(tomorrow)}      # lists can still change; re-check & overwrite
    print(f"[daily] today(BS)={bsdate.iso(today)} window={bsdate.iso(start)}..{bsdate.iso(tomorrow)}", flush=True)
    stats = scrape_dates(bsdate.daterange(start, tomorrow), force=False, refetch=refetch, git_push=a.git_push)
    print("[done]", stats)


def cmd_range(a):
    start = bsdate.parse_bs(a.start or HISTORICAL_START)
    end = bsdate.parse_bs(a.end or HISTORICAL_END)
    stats = scrape_dates(bsdate.daterange(start, end), force=a.force, git_push=a.git_push)
    print("[done]", stats)


def cmd_probe(a):
    """Saves raw HTML + screenshot + parsed summary of ONE date, to debug layout differences."""
    from .browser import Site
    out = ROOT / "probe"
    out.mkdir(exist_ok=True)
    with Site() as site:
        html = site.search(a.date)
        (out / f"{a.date}.html").write_text(html, encoding="utf-8")
        site.screenshot(str(out / f"{a.date}.png"))
    res = parse(html)
    summary = dict(date=a.date, heading_date=res.heading_date, cause_rows=len(res.causes),
                   judge_rows=len(res.judges), first_cause_row=res.causes[:1], first_judge_row=res.judges[:1])
    (out / f"{a.date}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def cmd_plan(a):
    """One matrix entry per BS year, so each year runs in its own 6-hour GitHub job."""
    start = bsdate.parse_bs(a.start or HISTORICAL_START)
    end = bsdate.parse_bs(a.end or HISTORICAL_END)
    inc = []
    for y in range(start.year, end.year + 1):
        s = max(start, bsdate.parse_bs(f"{y}-01-01"))
        e = min(end, bsdate.year_end(y))
        inc.append({"start": bsdate.iso(s), "end": bsdate.iso(e), "year": y})
    print(json.dumps({"include": inc}))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("daily", cmd_daily), ("range", cmd_range), ("probe", cmd_probe), ("plan", cmd_plan)):
        sp = sub.add_parser(name)
        sp.set_defaults(fn=fn)
        if name in ("range", "plan"):
            sp.add_argument("--start")
            sp.add_argument("--end")
        if name == "range":
            sp.add_argument("--force", action="store_true")
        if name in ("daily", "range"):
            sp.add_argument("--git-push", action="store_true")
        if name == "probe":
            sp.add_argument("--date", required=True)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
