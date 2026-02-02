import os
import json
import gspread
from google.oauth2.service_account import Credentials

# =====================
# ENV
# =====================
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
WATCH_SHEET = os.environ.get("WATCH_SHEET", "Logs")
STATS_SHEET = os.environ.get("STATS_SHEET", "Daily Stats")
STATUS_SHEET = os.environ.get("STATUS_SHEET", "__STATE")
SERVICE_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

# =====================
# AUTH
# =====================
creds_info = json.loads(SERVICE_JSON)
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
gc = gspread.authorize(credentials)

sheet = gc.open_by_key(SPREADSHEET_ID)

# =====================
# CONSTANTS
# =====================
DAILY_MSG_CELL = "B1"   # Daily stats Discord message ID
LAST_LOG_ROW_CELL = "A1"

DAILY_STATS_RANGE = "B7:C20"

# =====================
# GENERIC HELPERS
# =====================
def get_sheet_values(sheet_name):
    ws = sheet.worksheet(sheet_name)
    return ws.get_all_values()

def get_row_count(sheet_name):
    ws = sheet.worksheet(sheet_name)
    return len(ws.get_all_values())

# =====================
# DAILY STATS
# =====================
def get_daily_stats():
    ws = sheet.worksheet(STATS_SHEET)
    rows = ws.get(DAILY_STATS_RANGE)

    totals = {}
    total_items = 0

    for row in rows:
        if len(row) < 2:
            continue

        person = row[0].strip()
        if not person:
            continue

        try:
            qty = int(row[1])
        except (ValueError, TypeError):
            continue

        totals[person] = totals.get(person, 0) + qty
        total_items += qty

    sorted_rows = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    return sorted_rows, total_items

# =====================
# DAILY MESSAGE ID
# =====================
def get_last_daily_msg_id():
    ws = sheet.worksheet(STATS_SHEET)
    value = ws.acell(DAILY_MSG_CELL).value
    return int(value) if value and value.isdigit() else None

def save_last_daily_msg_id(msg_id):
    ws = sheet.worksheet(STATS_SHEET)
    ws.update(DAILY_MSG_CELL, [[str(msg_id)]])  # store as string

# =====================
# LOG STATE
# =====================
def get_last_processed_row():
    ws = sheet.worksheet(STATUS_SHEET)
    value = ws.acell(LAST_LOG_ROW_CELL).value
    return int(value) if value and value.isdigit() else 0

def set_last_processed_row(row_number):
    ws = sheet.worksheet(STATUS_SHEET)
    ws.update(LAST_LOG_ROW_CELL, [[str(row_number)]])

# =====================
# LOG DELTA FETCH
# =====================
def get_new_log_rows(last_row):
    ws = sheet.worksheet(WATCH_SHEET)
    values = ws.get_all_values()

    if not values or len(values) < 2:
        return [], last_row

    headers, data_rows = values[0], values[1:]

    if last_row >= len(data_rows):
        return [], last_row

    new_rows = data_rows[last_row:]
    new_rows = [r for r in new_rows if any(cell.strip() for cell in r if cell)]

    current_last_row = len(data_rows)
    return new_rows, current_last_row
