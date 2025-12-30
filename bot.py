
#SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"
#CHANNEL_ID = 1455146969579126951

import os
import asyncio
import discord
from discord.ext import commands, tasks
from sheets import get_daily_stats, get_row_count, get_sheet_values, DAILY_STATS_SHEET, LOGS_SHEET

DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
STATS_CHANNEL_ID = int(os.environ.get("STATS_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

last_known_log_rows = 0

# Build daily stats embed
def build_daily_stats_embed(rows, total):
    embed = discord.Embed(
        title=f"📅 Daily Stats - {datetime.utcnow():%A, %d %B %Y}",
        color=discord.Color.dark_teal()
    )
    table_text = ""
    for person, items in rows:
        table_text += f"**{person}** | {items}\n"

    embed.add_field(name="Stats", value=table_text if table_text else "No data available.", inline=False)
    embed.add_field(name="Total Sent", value=f"**{total}**", inline=False)
    return embed

# Slash command setup
@bot.command(name="dailystats")
async def dailystats(ctx):
    rows, total = get_daily_stats()
    embed = build_daily_stats_embed(rows, total)
    await ctx.send(embed=embed)

# Background task: daily stats at 9am UTC
@tasks.loop(minutes=1)
async def daily_stats_task():
    now = discord.utils.utcnow().astimezone()
    if now.hour == 9 and now.minute == 0:
        rows, total = get_daily_stats()
        embed = build_daily_stats_embed(rows, total)
        channel = bot.get_channel(STATS_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)

# Background task: watch Logs tab
@tasks.loop(seconds=60)
async def sheet_watch_task():
    global last_known_log_rows
    current_rows = get_row_count(LOGS_SHEET)
    if current_rows > last_known_log_rows:
        new_entries = get_sheet_values(LOGS_SHEET)[last_known_log_rows:]
        channel = bot.get_channel(STATS_CHANNEL_ID)
        msg = "🆕 **New entries added to Logs**\n"
        for row in new_entries:
            msg += " | ".join(row) + "\n"
        if channel:
            await channel.send(msg)
        last_known_log_rows = current_rows

@bot.event
async def on_ready():
    global last_known_log_rows
    print(f"✅ Logged in as {bot.user}")
    last_known_log_rows = get_row_count(LOGS_SHEET)
    daily_stats_task.start()
    sheet_watch_task.start()

bot.run(DISCORD_TOKEN)
