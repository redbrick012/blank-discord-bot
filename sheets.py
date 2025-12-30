import os
import gspread

# -------------------------
# Google Sheets Setup
# -------------------------
SHEET_ID = os.environ["SHEET_ID"]  # Spreadsheet ID
DAILY_STATS_TAB = "Daily Stats"
WATCH_SHEET = "logs"

def get_client():
    """Authenticate with Google Sheets using a service account dict."""
    creds = {
        "type": "service_account",
        "project_id": os.environ["GS_PROJECT_ID"],
        "private_key_id": os.environ["GS_PRIVATE_KEY_ID"],
        "private_key": os.environ["GS_PRIVATE_KEY"].replace("\\n", "\n"),
        "client_email": os.environ["GS_CLIENT_EMAIL"],
        "client_id": os.environ["GS_CLIENT_ID"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.environ["GS_CLIENT_CERT_URL"]
    }
    return gspread.service_account_from_dict(creds)

# -------------------------
# Fetch Sheet Data
# -------------------------
def get_sheet_values(sheet_id, tab_name):
    """Return all values from a sheet/tab."""
    client = get_client()
    sheet = client.open_by_key(sheet_id).worksheet(tab_name)
    return sheet.get_all_values()

def get_daily_stats():
    """
    Returns:
        rows: List of tuples (person, items_sent)
        total: Sum of all items_sent
    """
    sheet_values = get_sheet_values("Daily Stats", start_row=2, end_row=None)  # skip header
    rows = []
    total = 0
    for row in sheet_values:
        if len(row) < 2:
            continue
        person = row[0].strip()
        try:
            items_sent = int(row[1])
        except ValueError:
            continue  # skip invalid numbers
        rows.append((person, items_sent))
        total += items_sent
    return rows, total


def get_row_count(tab_name=WATCH_SHEET):
    """Return number of rows in a tab."""
    client = get_client()
    sheet = client.open_by_key(SHEET_ID).worksheet(tab_name)
    return len(sheet.get_all_values())
