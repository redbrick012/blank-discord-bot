import gspread
import os

def get_client():
    return gspread.service_account_from_dict({
        "type": "service_account",
        "project_id": os.environ["GS_PROJECT_ID"],
        "private_key_id": os.environ["GS_PRIVATE_KEY_ID"],
        "private_key": os.environ["GS_PRIVATE_KEY"].replace("\\n", "\n"),
        "client_email": os.environ["GS_CLIENT_EMAIL"],
        "client_id": os.environ["GS_CLIENT_ID"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": os.environ["GS_CLIENT_CERT_URL"],
    })

def get_daily_stats():
    gc = get_client()
    ws = gc.open_by_key(os.environ["SHEET_ID"]).worksheet("Daily Stats")

    data = ws.get("B4:C12")

    rows = []
    total = 0

    for row in data:
        if len(row) < 2:
            continue

        name = row[0].strip()
        value = int(row[1]) if row[1].isdigit() else 0

        if name:
            rows.append((name, value))
            total += value

    return rows, total

def get_row_count(sheet_name: str) -> int:
    gc = get_client()
    ws = gc.open_by_key(os.environ["SHEET_ID"]).worksheet(sheet_name)
    return len(ws.get_all_values())
