import os
import json
import gspread
from google.oauth2.service_account import Credentials

# ---------- CONFIG ----------
SHEET_ID = os.getenv("SHEET_ID")
WATCH_SHEET = "Logs"          # EXACT tab name
STATS_SHEET = "Daily Stats"   # EXACT tab name

if not SHEET_ID:
    raise RuntimeError("SHEET_ID not set")

# ---------- AUTH ----------
def get_client():
    """Return a gspread client using a single JSON secret."""
    creds_json = os.getenv("GOOGLE_CREDS_JSON")
    if not creds_json:
        raise RuntimeError("GOOGLE_CREDS_JSON not set")

    # Parse the JSON string from GitHub secret
    info = json.loads(creds_json)

    creds = Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )

    return gspread.authorize(creds)

# ---------- CORE ----------
def get_sheet(sheet_name):
    gc = get_client()
    sh = gc.open_by_key(SHEET_ID)

    try:
        return sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        raise Exception(f"❌ Sheet '{sheet_name}' not found")

def get_sheet_values(sheet_name, cell_range=None):
    ws = get_sheet(sheet_name)

    if cell_range:
        values = ws.get(cell_range)
    else:
        values = ws.get_all_values()

    print(f"[Sheets] Read {len(values)} rows from '{sheet_name}'")
    return values

def get_row_count(sheet_name):
    values = get_sheet_values(sheet_name)
    return len(values)

def get_daily_stats():
    ws = get_sheet(STATS_SHEET)

    # Table is B6:C20
    values = ws.get("B6:C20")

    rows = []
    total = 0

    for row in values:
        if len(row) < 2:
            continue

        name = row[0].strip()
        try:
            count = int(row[1])
        except ValueError:
            continue

        rows.append((name, count))
        total += count

    return rows, total
