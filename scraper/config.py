"""All settings in one place. Most can be overridden with environment variables."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
STATE_DIR = ROOT / "state"

SITE_URL = os.getenv("SITE_URL", "https://supremecourt.gov.np/weekly_dainik/pesi/daily/39")

# Project date rules (Bikram Sambat)
HISTORICAL_START = "2072-01-01"
HISTORICAL_END = "2083-07-19"
DAILY_START = "2083-07-20"

# File naming - copied exactly from the two model files supplied
CAUSE_FILE = "{iso}_Daily_Cause_List_KDC.csv"
JUDGES_FILE = "{iso}_Daily_Judges_List_KDC_.csv"   # trailing underscore, as in the model

# "model": registration date written as MM/DD/YYYY in Nepali digits (as in the model files)
# "site" : registration date written exactly as the website shows it (YYYY-MM-DD)
DATE_STYLE = os.getenv("DATE_STYLE", "model")

# The model Judges file ends with one empty row (",,,,,"). Kept for an exact match.
JUDGES_TRAILING_BLANK_ROW = os.getenv("JUDGES_TRAILING_BLANK_ROW", "1") == "1"

DELAY_BETWEEN_DATES = float(os.getenv("DELAY_BETWEEN_DATES", "1.0"))
RETRIES = int(os.getenv("RETRIES", "3"))
NAV_TIMEOUT_MS = int(os.getenv("NAV_TIMEOUT_MS", "90000"))

# Optional CSS selector overrides, only needed if the site layout differs from the screenshots
DATE_INPUT_SELECTOR = os.getenv("DATE_INPUT_SELECTOR", "")
SUBMIT_SELECTOR = os.getenv("SUBMIT_SELECTOR", "")

DAILY_MAX_LOOKBACK_DAYS = 60
