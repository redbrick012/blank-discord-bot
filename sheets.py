import os
import json
import gspread
from google.oauth2.service_account import Credentials

# ---------- CONFIG ----------
SHEET_ID = os.getenv("SHEET_ID")
WATCH_SHEET = "Logs"
STATS_SHEET = "Daily Stats"

if not SHEET_ID:
    raise RuntimeError("SHEET_ID not set")

# ---------- AUTH ----------
def get_client():
    creds_json = os.getenv("GOOGLE_CREDS_JSON")
    if not creds_json:
        raise RuntimeError("GOOGLE_CREDS_JSON not set")

    info = json.loads(creds_json)
    creds = Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
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
    return ws.get(cell_range) if cell_range else ws.get_all_values()

def get_row_count(sheet_name):
    return len(get_sheet_values(sheet_name))

def get_daily_stats():
    ws = get_sheet(STATS_SHEET)
    values = ws.get("B6:C20")
    rows, total = [], 0
    for row in values:
        if len(row) < 2: continue
        name = row[0].strip()
        try:
            count = int(row[1])
        except ValueError:
            continue
        rows.append((name, count))
        total += count
    return rows, total

# Optional: save/retrieve last daily stats message ID in sheet
def get_last_daily_msg_id():
    ws = get_sheet(STATS_SHEET)
    cell = ws.acell("E1").value  # store in E1
    return int(cell) if cell and cell.isdigit() else None

def save_last_daily_msg_id(msg_id):
    ws = get_sheet(STATS_SHEET)
    ws.update("E1", str(msg_id))
