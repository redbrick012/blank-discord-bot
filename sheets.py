import os
import gspread
from google.oauth2.service_account import Credentials

# Spreadsheet ID (from environment variable)
SHEET_ID = os.environ.get("SHEET_ID")

# Scopes required for gspread
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Name of sheets to use
DAILY_STATS_SHEET = "Daily Stats"
LOGS_SHEET = "Logs"

# Create the client
def get_client():
    creds_dict = {
        "type": os.environ.get("GS_TYPE"),
        "project_id": os.environ.get("GS_PROJECT_ID"),
        "private_key_id": os.environ.get("GS_PRIVATE_KEY_ID"),
        "private_key": os.environ.get("GS_PRIVATE_KEY").replace("\\n", "\n"),
        "client_email": os.environ.get("GS_CLIENT_EMAIL"),
        "client_id": os.environ.get("GS_CLIENT_ID"),
        "auth_uri": os.environ.get("GS_AUTH_URI"),
        "token_uri": os.environ.get("GS_TOKEN_URI"),
        "auth_provider_x509_cert_url": os.environ.get("GS_AUTH_PROVIDER_CERT_URL"),
        "client_x509_cert_url": os.environ.get("GS_CLIENT_CERT_URL"),
    }
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    return gspread.authorize(creds)

gc = get_client()

# Get all values from a sheet
def get_sheet_values(sheet_name, range_="A:Z"):
    try:
        sheet = gc.open_by_key(SHEET_ID).worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"❌ Sheet '{sheet_name}' not found!")
        return []

    values = sheet.get(range_)
    return values if values else []

# Get Daily Stats as a list of tuples and total
def get_daily_stats():
    rows = get_sheet_values(DAILY_STATS_SHEET, "B6:C11")
    result = []
    total = 0
    for row in rows:
        if len(row) < 2:
            continue
        person, items_sent = row[0], row[1]
        try:
            items_sent = int(items_sent)
        except ValueError:
            continue  # skip headers or invalid numbers
        result.append((person, items_sent))
        total += items_sent
    return result, total

# Get row count (used for watching Logs tab)
def get_row_count(sheet_name):
    values = get_sheet_values(sheet_name)
    return len(values)
