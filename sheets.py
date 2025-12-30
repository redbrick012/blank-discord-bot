import os
import gspread
from google.oauth2.service_account import Credentials

# --- Environment / Google Sheets Setup ---
SHEET_ID = os.environ["SHEET_ID"]  # Spreadsheet ID
WATCH_SHEET = "logs"               # Sheet to watch for new rows
STATS_SHEET = "Daily Stats"        # Sheet with daily stats

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
SERVICE_ACCOUNT_INFO = {
    "type": os.environ.get("GS_TYPE"),
    "project_id": os.environ.get("GS_PROJECT_ID"),
    "private_key_id": os.environ.get("GS_PRIVATE_KEY_ID"),
    "private_key": os.environ.get("GS_PRIVATE_KEY").replace("\\n", "\n"),
    "client_email": os.environ.get("GS_CLIENT_EMAIL"),
    "client_id": os.environ.get("GS_CLIENT_ID"),
    "auth_uri": os.environ.get("GS_AUTH_URI"),
    "token_uri": os.environ.get("GS_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.environ.get("GS_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.environ.get("GS_CLIENT_CERT_URL")
}

def get_client():
    """Authenticate and return a gspread client."""
    creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
    gc = gspread.authorize(creds)
    return gc

def get_sheet(sheet_name):
    """Return a worksheet object for a given sheet name."""
    gc = get_client()
    sh = gc.open_by_key(SHEET_ID)
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows=100, cols=20)
    return ws

def get_sheet_values(sheet_name, range_notation=None):
    """
    Returns all values in a sheet (or optional range) as a list of lists of strings.
    Example: range_notation="B6:C11"
    """
    worksheet = get_sheet(sheet_name)
    if range_notation:
        data = worksheet.get(range_notation)
    else:
        data = worksheet.get_all_values()
    return data or []

def get_row_count(sheet_name):
    """Return number of non-empty rows in a sheet."""
    values = get_sheet_values(sheet_name)
    return len(values)

def get_daily_stats():
    """
    Returns daily stats as list of tuples (person, items_sent) and the total.
    Expects range B6:C11 in 'Daily Stats' sheet.
    """
    rows = get_sheet_values(STATS_SHEET, "B6:C11")
    result = []
    total = 0
    for row in rows:
        if len(row) < 2:
            continue
        person, items_sent = row
        # skip header or empty rows
        if not person or person.lower() == "person":
            continue
        try:
            count = int(items_sent)
        except ValueError:
            count = 0
        result.append((person, count))
        total += count
    return result, total
