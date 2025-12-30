import os
import gspread
from google.oauth2.service_account import Credentials

# ===== Spreadsheet config =====
SHEET_ID = os.environ["SHEET_ID"]

STATS_SHEET = "Daily Stats"
WATCH_SHEET = "logs"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]

def get_client():
    creds = Credentials.from_service_account_info(
        {
            "type": os.environ["GS_TYPE"],
            "project_id": os.environ["GS_PROJECT_ID"],
            "private_key_id": os.environ["GS_PRIVATE_KEY_ID"],
            "private_key": os.environ["GS_PRIVATE_KEY"].replace("\\n", "\n"),
            "client_email": os.environ["GS_CLIENT_EMAIL"],
            "client_id": os.environ["GS_CLIENT_ID"],
            "auth_uri": os.environ["GS_AUTH_URI"],
            "token_uri": os.environ["GS_TOKEN_URI"],
            "auth_provider_x509_cert_url": os.environ["GS_AUTH_PROVIDER_CERT_URL"],
            "client_x509_cert_url": os.environ["GS_CLIENT_CERT_URL"],
        },
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def get_sheet(sheet_name):
    """
    Safely return worksheet or None if it does not exist.
    """
    gc = get_client()
    sh = gc.open_by_key(SHEET_ID)

    try:
        return sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        return None


def get_sheet_values(sheet_name, range_notation=None):
    """
    Returns values from a sheet or range.
    """
    ws = get_sheet(sheet_name)
    if not ws:
        return []

    if range_notation:
        return ws.get(range_notation)
    return ws.get_all_values()


def get_row_count(sheet_name):
    """
    Returns number of non-empty rows.
    """
    values = get_sheet_values(sheet_name)
    return len(values)


def get_daily_stats():
    """
    Reads B6:C11 from 'Daily Stats'
    Returns (rows, total)
    """
    values = get_sheet_values(STATS_SHEET, "B6:C11")

    rows = []
    total = 0

    for row in values:
        if len(row) < 2:
            continue

        name, value = row[0], row[1]

        try:
            value = int(value)
        except ValueError:
            continue

        rows.append((name, value))
        total += value

    return rows, total
