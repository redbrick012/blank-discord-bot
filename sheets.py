# sheets.py
import os
import json
import gspread
from google.oauth2.service_account import Credentials

# ---------- ENV ----------
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
WATCH_SHEET = os.environ.get("WATCH_SHEET", "Logs")
STATS_SHEET = os.environ.get("STATS_SHEET", "Stats")
STATUS_SHEET = os.environ.get("STATUS_SHEET", "__STATE")
SERVICE_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

# ---------- AUTH ----------
creds_info = json.loads(SERVICE_JSON)
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
gc = gspread.authorize(credentials)

# ---------- SHEETS ----------
sheet = gc.open_by_key(SPREADSHEET_ID)

# ---------- SHEET HELPERS ----------
def get_sheet_values(sheet_name):
    ws = sheet.worksheet(sheet_name)
    return ws.get_all_values()

def get_row_count(sheet_name):
    ws = sheet.worksheet(sheet_name)
    return len(ws.get_all_values())

# ---------- DAILY STATS ----------
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
        except ValueError:
            continue

        totals[person] = totals.get(person, 0) + qty
        total_items += qty

    sorted_rows = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    return sorted_rows, total_items

# ---------- LAST DAILY MESSAGE ----------
_LAST_MSG_CELL = "A1"

def get_last_daily_msg_id():
    ws = sheet.worksheet(STATS_SHEET)
    value = ws.acell(_LAST_MSG_CELL).value
    return int(value) if value and value.isdigit() else None

def save_last_daily_msg_id(msg_id):
    ws = sheet.worksheet(STATS_SHEET)
    ws.update(_LAST_MSG_CELL, [[msg_id]])  # wrap in list of lists)

# ---------- LAST LOGGED ROW ----------
_LAST_LOG_ROW_CELL = "A1"  # in __STATUS sheet

def get_last_processed_row():
    ws = sheet.worksheet(STATUS_SHEET)
    value = ws.acell(_LAST_LOG_ROW_CELL).value
    return int(value) if value and value.isdigit() else 1  # start after header

def set_last_processed_row(row_number):
    ws = sheet.worksheet(STATUS_SHEET)
    ws.update(_LAST_LOG_ROW_CELL, [[row_number]])  # <-- wrap in list of lists

# ---------- GET NEW LOG ROWS ----------
def get_new_log_rows(last_row):
    ws = sheet.worksheet(WATCH_SHEET)
    values = ws.get_all_values()
    headers, data_rows = values[0], values[1:]

    if last_row >= len(data_rows):
        return [], last_row  # nothing new

    new_rows = data_rows[last_row:]
    new_rows = [r for r in new_rows if any(cell.strip() for cell in r if cell)]
    current_last_row = len(data_rows)
    return new_rows, current_last_row
