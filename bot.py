
#SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"

import os
import discord
from discord.ext import commands, tasks
from datetime import datetime, time as dt_time

from sheets import get_sheet_data

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"
WORKSHEET_NAME = "Daily Stats"
DAILY_RANGE = "B4:C12"

CHANNEL_ID = 1455146969579126951  # Discord channel ID for daily posts

# -------------------------------------------------
# BOT SETUP
# -------------------------------------------------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------------------------------
# TABLE FORMATTER
# -------------------------------------------------
def format_table(data):
    if not data:
        return "No data."

    rows = [[str(cell) for cell in row] for row in data]

    col_widths = [
        max(len(row[i]) for row in rows)
        for i in range(len(rows[0]))
    ]

    formatted_rows = []
    for row in rows:
        formatted_rows.append(
            " | ".join(
                row[i].ljust(col_widths[i])
                for i in range(len(row))
            )
        )

    return "\n".join(formatted_rows)

# -------------------------------------------------
# SLASH COMMANDS
# -------------------------------------------------
@bot.tree.command(name="ping", description="Replies with Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 Pong!")

@bot.tree.command(
    name="dailystats",
    description="Show Daily Stats (B4:C12)"
)
async def dailystats(interaction: discord.Interaction):
    # Acknowledge immediately (prevents timeout)
    await interaction.response.defer()

    data = get_sheet_data(
        SPREADSHEET_ID,
        WORKSHEET_NAME,
        DAILY_RANGE
    )

    if not data:
        await interaction.followup.send("❌ No data found.")
        return

    table = format_table(data)
    await interaction.followup.send(
        f"📊 **Daily Stats**\n```{table}```"
    )

# -------------------------------------------------
# DAILY 9 AM UTC TASK
# -------------------------------------------------
last_post_date = None

@tasks.loop(minutes=1)
async def daily_post():
    global last_post_date

    now_utc = datetime.utcnow()
    today = now_utc.date()

    if now_utc.hour == 9 and now_utc.minute == 0:
        if last_post_date == today:
            return  # Already posted today

        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            print("❌ Daily post channel not found")
            return

        data = get_sheet_data(
            SPREADSHEET_ID,
            WORKSHEET_NAME,
            DAILY_RANGE
        )

        if not data:
            await channel.send("❌ No Daily Stats available.")
            return

        table = format_table(data)
        await channel.send(
            f"📅 **Daily Stats**\n```{table}```"
        )

        last_post_date = today

# -------------------------------------------------
# EVENTS
# -------------------------------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

    if not daily_post.is_running():
        daily_post.start()

# -------------------------------------------------
# RUN
# -------------------------------------------------
bot.run(DISCORD_TOKEN)
