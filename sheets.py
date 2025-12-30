import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials

WATCH_SHEET = "logs"  # The tab you want to watch

def get_client():
    scope = ["https://spreadsheets.google.com/feeds",
             "https://www.googleapis.com/auth/drive"]
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

def get_sheet_values(sheet_id, tab_name):
    client = get_client()
    sheet = client.open_by_key(sheet_id).worksheet(tab_name)
    return sheet.get_all_values()

def get_row_count(tab_name):
    client = get_client()
    sheet = client.open_by_key(os.environ["SHEET_ID"]).worksheet(tab_name)
    return len(sheet.get_all_values())
