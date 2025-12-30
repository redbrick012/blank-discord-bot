import os
import gspread

# -------------------------
# Google Sheets Setup
# -------------------------
SHEET_ID = os.environ["1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"]  # Spreadsheet ID
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

def get_daily_stats(tab_name=DAILY_STATS_TAB, range_start="B4", range_end="C12"):
    """Return list of tuples [(person, items_sent), ...] skipping headers."""
    client = get_client()
    sheet = client.open_by_key(SHEET_ID).worksheet(tab_name)
    values = sheet.get(f"{range_start}:{range_end}")
    
    result = []
    for row in values:
        if len(row) >= 2 and row[0] != "" and not row[0].lower().startswith("person"):
            person = row[0]
            items_sent = row[1] if row[1] != "" else "0"
            try:
                result.append((person, int(items_sent)))
            except ValueError:
                continue  # skip invalid numeric values
    return result

def get_row_count(tab_name=WATCH_SHEET):
    """Return number of rows in a tab."""
    client = get_client()
    sheet = client.open_by_key(SHEET_ID).worksheet(tab_name)
    return len(sheet.get_all_values())
