import os
import gspread
from google.oauth2.service_account import Credentials

# Constants
SCOPE = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SHEET_ID = os.environ["SHEET_ID"]  # Spreadsheet ID
DAILY_STATS_SHEET = "Daily Stats"
WATCH_SHEET = "Logs"

# Initialize Google Sheets client
def get_client():
    creds_dict = {
        "type": os.environ["GS_TYPE"],
        "project_id": os.environ["GS_PROJECT_ID"],
        "private_key_id": os.environ["GS_PRIVATE_KEY_ID"],
        "private_key": os.environ["GS_PRIVATE_KEY"].replace("\\n", "\n"),
        "client_email": os.environ["GS_CLIENT_EMAIL"],
        "client_id": os.environ["GS_CLIENT_ID"],
        "auth_uri": os.environ["GS_AUTH_URI"],
        "token_uri": os.environ["GS_TOKEN_URI"],
        "auth_provider_x509_cert_url": os.environ["GS_AUTH_PROVIDER_CERT_URL"],
        "client_x509_cert_url": os.environ["GS_CLIENT_CERT_URL"]
    }
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPE)
    return gspread.authorize(creds)

gc = get_client()

# Fetch values from a sheet
def get_sheet_values(sheet_name, start_row=1, end_row=None, start_col=1, end_col=None):
    sheet = gc.open_by_key(SHEET_ID).worksheet(sheet_name)
    range_notation = gspread.utils.rowcol_to_a1(start_row, start_col)
    if end_row and end_col:
        range_notation += f":{gspread.utils.rowcol_to_a1(end_row, end_col)}"
    elif end_row:
        range_notation += f":{gspread.utils.rowcol_to_a1(end_row, sheet.col_count)}"
    elif end_col:
        range_notation += f":{gspread.utils.rowcol_to_a1(sheet.row_count, end_col)}"
    return sheet.get(range_notation)

# Get daily stats rows and total
def get_daily_stats():
    rows_raw = get_sheet_values(DAILY_STATS_SHEET, start_row=6)  # skip header
    rows = []
    total = 0
    for row in rows_raw:
        if len(row) < 2:
            continue
        person = row[0].strip()
        try:
            items_sent = int(row[1])
        except ValueError:
            continue
        rows.append((person, items_sent))
        total += items_sent
    return rows, total

# Get the number of rows in a sheet
def get_row_count(sheet_name):
    sheet = gc.open_by_key(SHEET_ID).worksheet(sheet_name)
    return len(sheet.get_all_values())
