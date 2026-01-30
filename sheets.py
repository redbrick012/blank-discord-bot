import os
import json
import gspread
from google.oauth2.service_account import Credentials

# =====================
# ENVIRONMENT VARIABLES
# =====================
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
WATCH_SHEET = os.environ["WATCH_SHEET"]          # log sheet name
STATS_SHEET = os.environ.get("STATS_SHEET", "Stats")
STATUS_SHEET = "__STATE"                         # holds last processed row
SERVICE_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

# =====================
# GOOGLE AUTH
# =====================
creds_info = json.loads(SERVICE_JSON)
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)

gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID)

# =====================
# GENERIC HELPERS
# =====================
def get_sheet_values(sheet_name: str):
    """Return all values from a sheet"""
    ws = sheet.worksheet(sheet_name)
    return ws.get_all_values()

def get_row_count(sheet_name: str) -> int:
    ws = sheet.worksheet(sheet_name)
    return len(ws.get_all_values())

# =====================
# DAILY STATS
# =====================
def get_daily_stats():
    ws = sheet.worksheet(STATS_SHEET)
    rows = ws.get_all_values()[1:]  # skip header

    totals = {}
    total_items = 0

    for row in rows:
        if len(row) < 6:
            continue

        person = row[1].strip()
        try:
            qty = int(row[5])
        except (ValueError, TypeError):
            continue

        totals[person] = totals.get(person, 0) + qty
        total_items += qty

    sorted_rows = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    return sorted_rows, total_items

# =====================
# DAILY MESSAGE TRACKING
# =====================
_LAST_DAILY_MSG_CELL = "B1"

def get_last_daily_msg_id():
    ws = sheet.worksheet(STATUS_SHEET)
    value = ws.acell(_LAST_DAILY_MSG_CELL).value
    return int(value) if value and value.isdigit() else None

def save_last_daily_msg_id(message_id: int):
    ws = sheet.worksheet(STATUS_SHEET)
    ws.update(_LAST_DAILY_MSG_CELL, str(message_id))

# =====================
# LOG WATCH TRACKING
# =====================
_LAST_LOG_ROW_CELL = "A1"

def get_last_processed_row() -> int:
    """
    Reads __STATUS!A1
    This is the LAST LOG ROW ALREADY POSTED
    """
    ws = sheet.worksheet(STATUS_SHEET)
    value = ws.acell(_LAST_LOG_ROW_CELL).value
    return int(value) if value and value.isdigit() else 1  # start after header

def save_last_processed_row(row_number: int):
    """
    Saves the NEW last processed log row
    """
    ws = sheet.worksheet(STATUS_SHEET)
    ws.update(_LAST_LOG_ROW_CELL, str(row_number))
