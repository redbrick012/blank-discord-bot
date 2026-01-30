import os
import json
import gspread
from google.oauth2.service_account import Credentials

# =====================
# ENV
# =====================
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
if not SPREADSHEET_ID:
    raise RuntimeError("SPREADSHEET_ID not set")

SERVICE_ACCOUNT_INFO = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

# Sheet names
WATCH_SHEET = "Watch"
STATS_SHEET = "Stats"

# State cell (stores last processed row)
STATE_CELL = "Z1"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# =====================
# CLIENT
# =====================
creds = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO,
    scopes=SCOPES
)
client = gspread.authorize(creds)

# =====================
# HELPERS
# =====================
def get_sheet(sheet_name):
    return client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)

def get_sheet_values(sheet_name):
    return get_sheet(sheet_name).get_all_values()

def get_row_count(sheet_name):
    values = get_sheet_values(sheet_name)
    return len(values)

# =====================
# DAILY STATS
# =====================
def get_daily_stats():
    """
    Expects STATS_SHEET with:
    A = Name
    B = Count
    """
    ws = get_sheet(STATS_SHEET)
    rows = ws.get_all_values()[1:]  # skip header

    data = []
    total = 0

    for row in rows:
        if len(row) < 2:
            continue
        name = row[0]
        try:
            count = int(row[1])
        except ValueError:
            continue
        data.append((name, count))
        total += count

    return data, total

# =====================
# LAST ROW STATE (Sheet-based)
# =====================
def get_last_processed_row():
    ws = get_sheet(WATCH_SHEET)
    value = ws.acell(STATE_CELL).value
    try:
        return int(value)
    except (TypeError, ValueError):
        return 1  # default = header only

def save_last_processed_row(row_number: int):
    ws = get_sheet(WATCH_SHEET)
    ws.update(STATE_CELL, [[str(row_number)]])

# =====================
# DAILY MESSAGE ID (OPTIONAL)
# =====================
def get_last_daily_msg_id():
    ws = get_sheet(STATS_SHEET)
    val = ws.acell("Z1").value
    try:
        return int(val)
    except (TypeError, ValueError):
        return None

def save_last_daily_msg_id(message_id: int):
    ws = get_sheet(STATS_SHEET)
    ws.update("Z1", [[str(message_id)]])
