import os
import json
import gspread

# Tab names
WATCH_SHEET = "logs"
STATS_SHEET = "Daily Stats"

# Spreadsheet ID
SHEET_ID = os.environ.get("SHEET_ID")  # Put your Google Sheet ID here in env variables

# Build credentials from environment variables
service_account_info = {
    "type": os.environ.get("GS_TYPE"),
    "project_id": os.environ.get("GS_PROJECT_ID"),
    "private_key_id": os.environ.get("GS_PRIVATE_KEY_ID"),
    "private_key": os.environ.get("GS_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.environ.get("GS_CLIENT_EMAIL"),
    "client_id": os.environ.get("GS_CLIENT_ID"),
    "auth_uri": os.environ.get("GS_AUTH_URI"),
    "token_uri": os.environ.get("GS_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.environ.get("GS_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.environ.get("GS_CLIENT_CERT_URL"),
}

# Initialize client
def get_client():
    return gspread.service_account_from_dict(service_account_info)

# Get all values from a specific sheet/tab
def get_sheet_values(sheet_name, range_string=None):
    gc = get_client()
    sheet = gc.open_by_key(SHEET_ID).worksheet(sheet_name)
    if range_string:
        return sheet.get(range_string)
    return sheet.get_all_values()

# Get the number of rows in a sheet
def get_row_count(sheet_name):
    values = get_sheet_values(sheet_name)
    return len(values)

# Get the daily stats as a list of tuples and total
def get_daily_stats():
    rows = get_sheet_values(STATS_SHEET, "B4:C12")  # Adjust the range if needed
    result = []
    total = 0
    for row in rows:
        if len(row) < 2:
            continue
        person = row[0]
        items_sent = row[1]
        try:
            items_sent_int = int(items_sent)
        except ValueError:
            # Skip headers or empty values
            continue
        result.append((person, items_sent_int))
        total += items_sent_int
    return result, total
