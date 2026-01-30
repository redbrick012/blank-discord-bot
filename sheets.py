import os
import json
import gspread
from google.oauth2.service_account import Credentials

# ---------- ENV ----------
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
WATCH_SHEET = os.environ["WATCH_SHEET"]
STATS_SHEET = os.environ.get("STATS_SHEET", "Stats")
SERVICE_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

# ---------- AUTH ----------
creds_info = json.loads(SERVICE_JSON)
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
gc = gspread.authorize(credentials)
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

# ---------- LAST DAILY MESSAGE ID ----------
_LAST_MSG_CELL = "A1"

def get_last_daily_msg_id():
    ws = sheet.worksheet(STATS_SHEET)
    value = ws.acell(_LAST_MSG_CELL).value
    return int(value) if value and value.isdigit() else None

def save_last_daily_msg_id(msg_id):
    ws = sheet.worksheet(STATS_SHEET)
    ws.update(_LAST_MSG_CELL, str(msg_id))

# ---------- LAST LOGGED ROW ----------
_LAST_LOG_ROW_CELL = "A1"  # Tracks last processed row in WATCH_SHEET

def get_last_logged_row():
    ws = sheet.worksheet(WATCH_SHEET)
    value = ws.acell(_LAST_LOG_ROW_CELL).value
    return int(value) if value and value.isdigit() else 1  # start after header

def save_last_logged_row(row_number):
    ws = sheet.worksheet(WATCH_SHEET)
    ws.update(_LAST_LOG_ROW_CELL, str(row_number))
