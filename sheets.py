import os
import json
import gspread
from google.oauth2.service_account import Credentials

def get_sheet_data(spreadsheet_id, worksheet_name, cell_range=None):
    """
    Pulls data from a Google Sheet worksheet.
    If cell_range is provided, only that range is returned.
    """
    try:
        creds_json = json.loads(os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON"))

        scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        credentials = Credentials.from_service_account_info(creds_json, scopes=scopes)

        client = gspread.authorize(credentials)
        sheet = client.open_by_key(spreadsheet_id).worksheet(worksheet_name)

        if cell_range:
            # Returns a 2D list of values
            return sheet.get(cell_range)
        else:
            return sheet.get_all_records()
    except Exception as e:
        print("Error reading Google Sheet:", e)
        return []
