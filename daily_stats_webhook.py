import os
import json
import requests
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# =====================
# ENV
# =====================
STATS_WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
SERVICE_ACCOUNT_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]

STATS_SHEET = os.environ.get("STATS_SHEET", "Daily Stats")
DAILY_MSG_CELL = "B1"
DAILY_STATS_RANGE = "B7:C20"

# =====================
# GOOGLE SHEETS SETUP
# =====================
creds_info = json.loads(SERVICE_ACCOUNT_JSON)
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
gc = gspread.authorize(creds)

sheet = gc.open_by_key(SPREADSHEET_ID)
ws = sheet.worksheet(STATS_SHEET)

# =====================
# HELPERS
# =====================
def get_daily_stats():
    rows = ws.get(DAILY_STATS_RANGE)
    totals = {}
    total_items = 0

    for row in rows:
        if len(row) < 2:
            continue
        person = row[0].strip()
        if not person:
            continue
        try:
            qty = int(row[1])
        except (ValueError, TypeError):
            continue
        totals[person] = totals.get(person, 0) + qty
        total_items += qty

    sorted_rows = sorted(totals.items(), key=lambda x: x[1], reverse=True)
    return sorted_rows, total_items

def build_embed(rows, total):
    yesterday = datetime.utcnow() - timedelta(days=1)
    lines = ["```", f"{'Person':<15} | {'Items':>6}", "─" * 26]
    for name, count in rows:
        lines.append(f"{name:<15} | {count:>6}")
    lines.append("─" * 26)
    lines.append(f"{'Total':<15} | {total:>6}")
    lines.append("```")

    embed = {
        "title": f"📊 Daily Stats – {yesterday.strftime('%A %d %B %Y')}",
        "description": "\n".join(lines),
        "color": 0x2ecc71,
        "footer": {"text": "Auto-refresh via GitHub Actions"},
        "timestamp": datetime.utcnow().isoformat()
    }
    return embed

def get_last_message_id():
    val = ws.acell(DAILY_MSG_CELL).value
    return int(val) if val and val.isdigit() else None

def save_last_message_id(msg_id):
    ws.update(DAILY_MSG_CELL, [[str(msg_id)]])

# =====================
# SEND OR EDIT WEBHOOK
# =====================
def send_webhook(embed):
    last_msg_id = get_last_message_id()
    payload = {"embeds": [embed]}
    headers = {"Content-Type": "application/json"}

    # Try to edit existing message
    if last_msg_id:
        edit_url = f"{DISCORD_WEBHOOK_URL}/messages/{last_msg_id}"
        r = requests.patch(edit_url, json=payload, headers=headers)
        if r.status_code == 200:
            print(f"🔁 Edited existing message {last_msg_id}")
            return last_msg_id
        else:
            print(f"⚠️ Edit failed ({r.status_code}), posting new message")

    # Post new message
    r = requests.post(DISCORD_WEBHOOK_URL, json=payload, headers=headers)
    if r.status_code in (200, 204):
        new_msg_id = r.json().get("id") if r.status_code == 200 else None
        if new_msg_id:
            save_last_message_id(new_msg_id)
        print(f"🆕 Posted new message {new_msg_id}")
        return new_msg_id
    else:
        raise RuntimeError(f"❌ Discord API error {r.status_code}: {r.text}")

# =====================
# MAIN
# =====================
def main():
    rows, total = get_daily_stats()
    if not rows:
        print("⚠️ No stats found")
        return
    embed = build_embed(rows, total)
    send_webhook(embed)

if __name__ == "__main__":
    main()
