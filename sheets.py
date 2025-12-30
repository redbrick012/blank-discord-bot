import os
import gspread
from datetime import datetime

# Spreadsheet and sheets
SHEET_ID = os.environ.get("SHEET_ID")
STATS_SHEET = "Daily Stats"
LOGS_SHEET = "Logs"

# Google service account credentials
GS_CREDS = {
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

def get_client():
    """Authenticate and return gspread client."""
    return gspread.service_account_from_dict(GS_CREDS)

def get_sheet(sheet_name):
    """Return worksheet object."""
    client = get_client()
    sheet = client.open_by_key(SHEET_ID)
    return sheet.worksheet(sheet_name)

def get_sheet_values(sheet_name, range_notation="B6:C11"):
    """
    Returns all values in a sheet (or optional range).
    Returns as list of lists of strings.
    """
    worksheet = get_sheet(sheet_name)
    if range_notation:
        return worksheet.get(range_notation)
    else:
        return worksheet.get_all_values()

def get_row_count(sheet_name):
    """Return number of rows with content."""
    values = get_sheet_values(sheet_name)
    return len(values)

def get_daily_stats():
    """
    Reads the Daily Stats sheet and returns:
        - list of tuples [(person, items_sent), ...]
        - total sent (int)
    Skips header row.
    """
    values = get_sheet_values(STATS_SHEET)

    result = []
    total = 0

    if not values or len(values) < 2:
        return result, total

    for row in values[1:]:  # skip header
        if len(row) < 2:
            continue
        person = row[0].strip()
        items_sent = row[1].strip()
        try:
            items_sent_int = int(items_sent)
        except ValueError:
            items_sent_int = 0
        result.append((person, items_sent_int))
        total += items_sent_int

    return result, total
