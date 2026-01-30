import os
import json
import gspread
from google.oauth2.service_account import Credentials

# ---------- ENV ----------
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
WATCH_SHEET = os.environ["WATCH_SHEET"]          # log sheet
STATUS_SHEET = "__STATE"
SERVICE_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

LAST_ROW_CELL = "A1"  # __STATUS!A1

# ---------- AUTH ----------
creds_info = json.loads(SERVICE_JSON)
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(creds_info, scopes=scopes)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SPREADSHEET_ID)

# ---------- STATUS HELPERS ----------
def get_last_processed_row():
    ws = sheet.worksheet(STATUS_SHEET)
    value = ws.acell(LAST_ROW_CELL).value
    return int(value) if value and value.isdigit() else 1  # start after header

def save_last_processed_row(row_number: int):
    ws = sheet.worksheet(STATUS_SHEET)
    ws.update(LAST_ROW_CELL, str(row_number))

# ---------- LOG HELPERS ----------
def get_new_log_rows():
    """
    Returns (new_rows, new_last_row)
    """
    ws = sheet.worksheet(WATCH_SHEET)
    values = ws.get_all_values()

    if len(values) <= 1:
        return [], get_last_processed_row()

    last_row = get_last_processed_row()
    data_rows = values[1:]  # skip header

    if last_row >= len(values):
        return [], last_row

    new_rows = data_rows[last_row:]
    new_rows = [
        row for row in new_rows
        if any(cell.strip() for cell in row if cell)
    ]

    return new_rows, len(values)
