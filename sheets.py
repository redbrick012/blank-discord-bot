import os
import gspread
from google.oauth2.service_account import Credentials

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
LOG_SHEET_NAME = "Logs"
STATUS_SHEET_NAME = "__STATE"
STATUS_CELL = "A1"


def get_client():
    creds = Credentials.from_service_account_file(
        "service_account.json",
        scopes=SCOPES
    )
    return gspread.authorize(creds)


def get_last_processed_row():
    client = get_client()
    sheet = client.open_by_key(SPREADSHEET_ID)
    status_ws = sheet.worksheet(STATUS_SHEET_NAME)

    value = status_ws.acell(STATUS_CELL).value
    return int(value) if value and value.isdigit() else 1


def set_last_processed_row(row_number: int):
    client = get_client()
    sheet = client.open_by_key(SPREADSHEET_ID)
    status_ws = sheet.worksheet(STATUS_SHEET_NAME)

    status_ws.update(STATUS_CELL, str(row_number))


def get_new_log_rows(last_row: int):
    client = get_client()
    sheet = client.open_by_key(SPREADSHEET_ID)
    log_ws = sheet.worksheet(LOG_SHEET_NAME)

    current_last_row = len(log_ws.get_all_values())

    if current_last_row <= last_row:
        return [], current_last_row

    # Fetch ONLY new rows (1-based indexing)
    start = last_row + 1
    end = current_last_row

    rows = log_ws.get(f"A{start}:Z{end}")
    return rows, current_last_row
