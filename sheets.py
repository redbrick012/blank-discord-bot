import os
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

# =====================
# ENVIRONMENT VARIABLES
# =====================
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
WATCH_SHEET = os.environ["WATCH_SHEET"]
SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

# =====================
# GOOGLE SHEETS CLIENT
# =====================
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(
    json.loads(SERVICE_ACCOUNT_JSON),
    scopes=SCOPES
)

service = build("sheets", "v4", credentials=creds)
sheet = service.spreadsheets()


# =====================
# LAST PROCESSED ROW
# =====================
LAST_ROW_CELL = f"{WATCH_SHEET}!Z1"


def get_last_processed_row() -> int:
    """
    Reads the last processed row number from Z1.
    Defaults to 1 (header row) if empty.
    """
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=LAST_ROW_CELL
    ).execute()

    values = result.get("values", [])
    if not values or not values[0]:
        return 1

    try:
        return int(values[0][0])
    except ValueError:
        return 1


def set_last_processed_row(row_number: int):
    """
    Writes the last processed row number to Z1.
    """
    sheet.values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=LAST_ROW_CELL,
        valueInputOption="RAW",
        body={"values": [[row_number]]}
    ).execute()


# =====================
# READ NEW ROWS
# =====================
def get_all_rows():
    """
    Returns all rows in the watch sheet.
    """
    result = sheet.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=WATCH_SHEET
    ).execute()

    return result.get("values", [])


def get_new_rows():
    """
    Returns only rows that have not yet been processed.
    """
    all_rows = get_all_rows()
    last_row = get_last_processed_row()

    # Google Sheets rows are 1-indexed
    # Skip header (row 1)
    start_index = max(last_row, 1)

    new_rows = all_rows[start_index:]

    return new_rows, len(all_rows)
