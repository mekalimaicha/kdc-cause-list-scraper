# KDC (Kathmandu District Court) Daily Cause List Scraper

Source: https://supremecourt.gov.np/weekly_dainik/pesi/daily/39

For every Nepali (B.S.) date it saves two files, inside a folder for the year:

```
data/2083/2083-07-19_Daily_Cause_List_KDC.csv      (one row per case, 13 columns)
data/2083/2083-07-19_Daily_Judges_List_KDC_.csv    (one row per judge: पेशी / फैसला / आदेश / स्थगित)
```
Dates with no list (public holidays etc.) produce no file; they are remembered in `state/no_data/<year>.txt`.

| Mode | What it does |
|---|---|
| `historical` | 2072-01-01 → 2083-07-19, one parallel job per year (resumable: just run again) |
| `daily` | catch-up from 2083-07-20, re-checks today + tomorrow. Scheduled 8 PM NPT, retried every 2 h until 6 AM |
| `range` | any custom start/end date (tick *force* to overwrite) |
| `probe` | debug: saves the page HTML + screenshot of one date as a downloadable artifact |

## A. Upload to GitHub
1. github.com → **New repository** (name e.g. `kdc-cause-list`), **Private** recommended → Create.
2. Unzip this project. On the repo page click **Add file → Upload files**, drag in *everything inside* the folder
   (including the hidden `.github` folder – if your browser skips it, use Git instead, see below) → **Commit changes**.
   Check that `.github/workflows/scrape.yml` is visible in the repo.
3. **Settings → Actions → General → Workflow permissions → Read and write permissions → Save.** (essential, otherwise it cannot save CSVs)

Git alternative: `git init && git add . && git commit -m init && git branch -M main && git remote add origin <repo-url> && git push -u origin main`

## B. First test (do this before the big run)
1. **Actions → Scrape KDC Daily Cause List → Run workflow**, mode **probe**, start_date `2083-07-18` → Run.
2. When green, open the run → **Artifacts → probe**. Check `2083-07-18_summary.json` shows `cause_rows` > 0 and `judge_rows` > 0,
   and compare the `.png` with the website.
3. If it fails or shows 0 rows, send me the artifact (html + png + log) and I will adjust the selectors.
   Also the court site may block foreign IPs (GitHub servers are in the USA) – see "If GitHub is blocked" below.

## C. Historical download (2072-01-01 → 2083-07-19)
**Actions → Run workflow → mode `historical` → Run.** 12 yearly jobs run (3 at a time), committing every 40 dates.
If some job hits the 6-hour limit, simply run `historical` again – existing dates are skipped.
Dates that failed are listed in `state/failed/<year>.txt`; re-running retries them.

## D. Daily automatic run
Already configured in the workflow: 8:00 PM Nepal time, plus retries at 10 PM, 12 AM, 2 AM, 4 AM, 6 AM
(lists published late are picked up; unchanged data is not re-committed). Manual run any time: **Run workflow → daily**.
Note: GitHub pauses scheduled workflows after 60 days of no repo activity in *public* repos; the daily commits prevent this.

## E. Get the files into `F:\MEGA\Advocate Mr. Pokhrel\Cause List Scarping`
GitHub cannot push into a laptop, so the laptop **pulls**:
1. Install Git for Windows (git-scm.com). For a private repo, the first `git clone` opens a browser login – sign in once.
2. Copy the `laptop` folder to e.g. `C:\CauseListTools\`.
3. Open `sync_to_laptop.ps1` in Notepad, set `$RepoUrl` to your repo URL (and `$Branch` if not `main`). Save.
4. Double-click `sync_now.bat` – the year folders (2072 … 2083) appear in your MEGA folder.
5. Right-click `install_schedule.ps1` → **Run with PowerShell** (once). It syncs daily at 7:30 AM and whenever you log on.
   If PowerShell refuses scripts: open PowerShell and run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
Log file: `C:\Users\<you>\CauseListSync.log`. Files are only added/updated in MEGA, never deleted.

## If GitHub is blocked by the court site
Symptoms: probe times out / empty page. Fix: use a **self-hosted runner** on your own Nepal laptop
(Settings → Actions → Runners → New self-hosted runner), and change `runs-on: ubuntu-latest` to `runs-on: self-hosted`
in the `scrape` job. Everything else stays the same.

## Settings (environment variables / `scraper/config.py`)
`DATE_STYLE` = `model` (registration date as `०७/१८/२०८३`, like your model files) or `site` (`२०८३-०७-१८`).
`DELAY_BETWEEN_DATES` (default 1 s), `DATE_INPUT_SELECTOR` / `SUBMIT_SELECTOR` (only if the page layout differs).

## Tests
`pip install -r requirements.txt && python -m pytest` – rebuilds a page from your two model CSVs and checks the output is identical.
