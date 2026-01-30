from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import os
import json

SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SERVICE_ACCOUNT_INFO = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_INFO,
    scopes=SCOPES
)

service = build("sheets", "v4", credentials=creds)

# ---------- CONSTANTS ----------
STATE_SHEET = "__STATE"
STATE_CELL = "A1"

# ---------- HELPERS ----------
def get_sheet_values(sheet_name):
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=sheet_name
    ).execute()
    return result.get("values", [])

def get_row_count(sheet_name):
    values = get_sheet_values(sheet_name)
    return len(values)

# ---------- STATE ----------
def get_last_processed_row():
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{STATE_SHEET}!{STATE_CELL}"
    ).execute()

    values = result.get("values", [])
    try:
        return int(values[0][0])
    except Exception:
        return 1  # safe default

def save_last_processed_row(row_number):
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f"{STATE_SHEET}!{STATE_CELL}",
        valueInputOption="RAW",
        body={"values": [[str(row_number)]]}
    ).execute()
