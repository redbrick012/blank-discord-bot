import os
import discord
from discord.ext import tasks, commands
from datetime import datetime, time, timedelta
import asyncio

from sheets import (
    get_daily_stats, get_row_count, get_sheet_values,
    WATCH_SHEET, STATS_SHEET,
    get_last_daily_msg_id, save_last_daily_msg_id
)

# ---------- ENV ----------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
STATS_CHANNEL_ID = int(os.getenv("STATS_CHANNEL_ID", 0))
LOGS_CHANNEL_ID = int(os.getenv("LOGS_CHANNEL_ID", 0))

if not DISCORD_TOKEN:
    raise RuntimeError("DISCORD_TOKEN not set")

# ---------- DISCORD SETUP ----------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# Track last rows for Logs
last_known_rows = 0
WATCH_COLUMNS = [0, 1, 2, 4, 5]  # A,B,C,E,F

# ---------- EMBED BUILDERS ----------
def bold_text(text):
    return text.translate(str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"
        "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘷𝘄𝘅𝘆𝘇"
    ))

def build_daily_stats_embed(rows, total):
    yesterday = datetime.utcnow() - timedelta(days=1)
    lines = ["```", f"{bold_text('Person'):<15} | {bold_text('Items Sent'):>10}", "═" * 28]
    for person, count in rows:
        lines.append(f"{person:<15} | {count:>10}")
    lines.append("═" * 28)
    lines.append(f"💰 {bold_text('Total Sent'):<13} | {total:>10}")
    lines.append("```")

    embed = discord.Embed(
        title=f"📅 Daily Stats – {yesterday.strftime('%A, %d %B %Y')}",
        color=discord.Color.green()
    )
    embed.add_field(name="Daily Breakdown", value="\n".join(lines), inline=False)
    return embed

def build_log_table(headers, rows):
    col_widths = [max(len(headers[col]), *(len(row[col]) if col < len(row) and row[col] else 1 for row in rows)) for col in WATCH_COLUMNS]
    header_line = " | ".join((headers[col] if col < len(headers) else f"Col {col+1}").ljust(col_widths[i]) for i, col in enumerate(WATCH_COLUMNS))
    separator_line = "─" * len(header_line)
    row_lines = []
    for row in rows:
        line = " | ".join((row[col] if col < len(row) and row[col] else "—").ljust(col_widths[i]) for i, col in enumerate(WATCH_COLUMNS))
        row_lines.append(line)
    return "```\n" + header_line + "\n" + separator_line + "\n" + "\n".join(row_lines) + "\n```"

# ---------- SLASH COMMANDS ----------
@bot.tree.command(name="dailystats", description="Show today's daily stats")
async def dailystats(interaction: discord.Interaction):
    await interaction.response.defer()
    rows, total = get_daily_stats()
    embed = build_daily_stats_embed(rows, total)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="lastlog", description="Show log entries from last hour")
async def lastlog(interaction: discord.Interaction):
    await interaction.response.defer()
    values = await asyncio.to_thread(get_sheet_values, WATCH_SHEET)
    if not values or len(values) < 2:
        await interaction.followup.send("No log entries found.")
        return
    headers, data_rows = values[0], values[1:]
    recent_rows = data_rows[-100:]
    new_rows = [r for r in recent_rows if any(c.strip() for c in r if c)]
    if not new_rows:
        await interaction.followup.send("No log entries found.")
        return
    embeds = []
    for row in new_rows:
        embed = discord.Embed(color=discord.Color.orange(), timestamp=datetime.utcnow())
        for i, col in enumerate(WATCH_COLUMNS):
            col_name = headers[col] if col < len(headers) else f"Col {col+1}"
            col_value = row[col] if col < len(row) and row[col] else "—"
            embed.add_field(name=col_name, value=col_value, inline=True)
        embeds.append(embed)
    for i in range(0, len(embeds), 10):
        await interaction.followup.send(embeds=embeds[i:i+10])

# ---------- TASKS ----------
@tasks.loop(time=time(hour=9, minute=0, second=0))
async def daily_stats_task():
    channel = bot.get_channel(STATS_CHANNEL_ID)
    if not channel:
        print("Stats channel not found")
        return
    rows, total = get_daily_stats()
    embed = build_daily_stats_embed(rows, total)

    message_id = get_last_daily_msg_id()
    try:
        if message_id:
            msg = await channel.fetch_message(message_id)
            await msg.edit(embed=embed)
            print("✅ Daily stats updated")
            return
    except discord.NotFound:
        pass
    msg = await channel.send(embed=embed)
    save_last_daily_msg_id(msg.id)
    print("✅ Daily stats message created")

@tasks.loop(minutes=15)
async def sheet_watch_task():
    global last_known_rows
    print(f"🕐 sheet_watch_task tick {datetime.utcnow().strftime('%H:%
