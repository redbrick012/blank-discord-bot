
#SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"

import os
import discord
from discord.ext import commands, tasks
from sheets import get_sheet_data
from datetime import datetime, time as dt_time

# ----------------------------
# CONFIGURATION
# ----------------------------
SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"  # replace with your Google Sheet ID
WORKSHEET_NAME = "Daily Stats"
CHANNEL_ID = 1455146969579126951  # replace with your Discord channel ID for daily posts

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ----------------------------
# SLASH COMMANDS
# ----------------------------
@bot.tree.command(name="ping", description="Replies with Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="sheet", description="Shows first row of Daily Stats")
async def sheet(interaction: discord.Interaction):
    data = get_sheet_data(SPREADSHEET_ID, WORKSHEET_NAME)

    if not data:
        await interaction.response.send_message("No data found or error reading sheet.")
        return

    first_row = data[0]
    formatted = "\n".join(f"{k}: {v}" for k, v in first_row.items())
    await interaction.response.send_message(f"First row:\n{formatted}")

@bot.tree.command(name="dailyrange", description="Shows B4:C12 from Daily Stats sheet")
async def dailyrange(interaction: discord.Interaction):
    data = get_sheet_data(SPREADSHEET_ID, WORKSHEET_NAME, "B4:C12")

    if not data:
        await interaction.response.send_message("No data found.")
        return

    table = format_table(data)
    await interaction.response.send_message(f"```\n{table}\n```")
# ----------------------------
# DAILY TASK
# ----------------------------
@tasks.loop(minutes=1)
async def daily_post():
    now = datetime.utcnow()  # UTC time; adjust if needed
    target = dt_time(hour=09, minute=0)  # 20:00 = 8 PM UTC

    if now.time().hour == target.hour and now.time().minute == target.minute:
        channel = bot.get_channel(CHANNEL_ID)
        if channel:
            data = get_sheet_data(SPREADSHEET_ID, WORKSHEET_NAME, "B4:C12")
            if not data:
                await channel.send("No data found for today.")
                return
            formatted = "\n".join(" | ".join(str(cell) for cell in row) for row in data)
            await channel.send(f"Daily Stats:\n```\n{formatted}\n```")
        else:
            print("Channel not found for daily post.")

# ----------------------------
# EVENTS
# ----------------------------
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (slash commands synced)")
    daily_post.start()  # start daily loop

# ----------------------------
# RUN BOT
# ----------------------------
bot.run(os.getenv("DISCORD_TOKEN"))
