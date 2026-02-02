# daily_stats_webhook.py
import os
import json
import requests
from datetime import datetime, timedelta
import gspread

# =====================
# ENV
# =====================
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]
SPREADSHEET_ID = os.environ["SPREADSHEET_ID"]
STATS_SHEET = os.environ.get("STATS_SHEET", "Daily Stats")
SERVICE_JSON = os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
DAILY_MSG_CELL = "B1"  # where we store the last Discord message ID
DAILY_STATS_RANGE = "B7:C20"

# =====================
# GOOGLE SHEETS SETUP
# =====================
SERVICE_ACCOUNT = json.loads(SERVICE_JSON)
gc = gspread.service_account_from_dict(SERVICE_ACCOUNT)
sh = gc.open_by_key(SPREADSHEET_ID)
ws = sh.worksheet(STATS_SHEET)

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

def get_last_message_id():
    val = ws.acell(DAILY_MSG_CELL).value
    return int(val) if val and val.isdigit() else None

def save_last_message_id(msg_id):
    ws.update(DAILY_MSG_CELL, [[str(msg_id)]])

def build_daily_embed(rows, total):
    yesterday = datetime.utcnow() - timedelta(days=1)
    lines = ["```", f"{'Person':<15} | {'Items Sent':>10}", "═" * 28]
    for person, count in rows:
        lines.append(f"{person:<15} | {count:>10}")
    lines.append("═" * 28)
    lines.append(f"💰 {'Total Sent':<13} | {total:>10}")
    lines.append("```")

    embed = {
        "title": f"📅 Daily Stats – {yesterday.strftime('%A, %d %B %Y')}",
        "color": 0x2ecc71,  # green
        "fields": [{"name": "Daily Breakdown", "value": "\n".join(lines), "inline": False}],
        "timestamp": datetime.utcnow().isoformat()
    }
    return embed

# =====================
# SEND OR EDIT WEBHOOK
# =====================
def send_webhook(embed):
    last_msg_id = get_last_message_id()
    payload = {"embeds": [embed]}
    headers = {"Content-Type": "application/json"}

    # Try edit existing message first
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
    if r.status_code in (200, 201, 204):
        new_msg_id = None
        try:
            new_msg_id = r.json().get("id")
        except Exception:
            pass  # Discord returned 204 No Content

        if new_msg_id:
            save_last_message_id(new_msg_id)
            print(f"🆕 Posted new message {new_msg_id} and saved to B1")
        else:
            print("🆕 Posted new message (ID not returned, B1 not updated)")

        return new_msg_id
    else:
        raise RuntimeError(f"❌ Discord API error {r.status_code}: {r.text}")

# =====================
# MAIN
# =====================
def main():
    rows, total = get_daily_stats()
    if not rows:
        print("⚠️ No daily stats rows found")
        return

    embed = build_daily_embed(rows, total)
    send_webhook(embed)

if __name__ == "__main__":
    main()
