import os
import json
import gspread
from google.oauth2.service_account import Credentials

def get_sheet_data(spreadsheet_id, worksheet_name):
    """
    Pulls all records from a Google Sheet worksheet.

    Returns a list of dicts.
    """
    try:
        creds_json = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))

        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        credentials = Credentials.from_service_account_info(creds_json, scopes=scopes)

        client = gspread.authorize(credentials)
        sheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)

        return sheet.get_all_records()
    except Exception as e:
        print("Error reading Google Sheet:", e)
        return []
