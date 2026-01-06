import os
import gspread
from google.oauth2.service_account import Credentials

# ---------- CONFIG ----------
SHEET_ID = os.environ["SHEET_ID"]

WATCH_SHEET = "Logs"          # EXACT tab name
STATS_SHEET = "Daily Stats"   # EXACT tab name

# ---------- AUTH ----------
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
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"],
    )
    return gspread.authorize(creds)

# ---------- CORE ----------
def get_sheet(sheet_name):
    gc = get_client()
    sh = gc.open_by_key(SHEET_ID)

    try:
        return sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        raise Exception(f"❌ Sheet '{sheet_name}' not found")

def get_sheet_values(sheet_name, cell_range=None):
    ws = get_sheet(sheet_name)

    if cell_range:
        values = ws.get(cell_range)
    else:
        values = ws.get_all_values()

    # 🔍 Debug visibility
    print(f"[Sheets] Read {len(values)} rows from '{sheet_name}'")

    return values

def get_row_count(sheet_name):
    values = get_sheet_values(sheet_name)
    return len(values)

def get_daily_stats():
    ws = get_sheet(STATS_SHEET)

    # Table is B6:C15
    values = ws.get("B6:C14")

    rows = []
    total = 0

    for row in values:
        if len(row) < 2:
            continue

        name = row[0].strip()
        try:
            count = int(row[1])
        except ValueError:
            continue

        rows.append((name, count))
        total += count

    return rows, total
