import os
import discord
from discord.ext import tasks, commands
from datetime import datetime, time, timedelta
import asyncio

from sheets import (
    get_daily_stats,
    get_row_count,
    get_sheet_values,
    WATCH_SHEET,
    STATS_SHEET,
    get_last_daily_msg_id,
    save_last_daily_msg_id,
    get_last_logged_row,
    save_last_logged_row
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

# ---------- EMBED HELPERS ----------
def bold_text(text):
    return text.translate(str.maketrans(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
        "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"
        "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘃𝘄𝘅𝘆𝘇"
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

def build_log_embed(rows):
    embed = discord.Embed(title="📄 New Log Entries", color=discord.Color.orange(), timestamp=datetime.utcnow())
    for row in rows:
        name = row[7] if len(row) > 7 else "Unknown"
        qty = row[5] if len(row) > 5 else "0"
        item = row[4] if len(row) > 4 else "—"
        timestamp = row[0] if len(row) > 0 else datetime.utcnow().strftime("%d/%m/%Y %H:%M:%S")
        embed.add_field(name=f"{name} • {item}", value=f"QTY: {qty}\nTime: {timestamp}", inline=False)
    return embed

# Split large log embeds to avoid Discord limit
MAX_FIELDS_PER_EMBED = 10
async def send_log_rows(channel, rows):
    for i in range(0, len(rows), MAX_FIELDS_PER_EMBED):
        embed = build_log_embed(rows[i:i+MAX_FIELDS_PER_EMBED])
        await channel.send(embed=embed)

# ---------- SLASH COMMANDS ----------
@bot.tree.command(name="dailystats", description="Show today's daily stats")
async def dailystats(interaction: discord.Interaction):
    await interaction.response.defer()
    rows, total = get_daily_stats()
    embed = build_daily_stats_embed(rows, total)
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="lastlog", description="Show recent log entries")
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
    await send_log_rows(interaction.channel, new_rows)

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

@tasks.loop(minutes=1)
async def sheet_watch_task():
    print(f"🕐 sheet_watch_task tick {datetime.utcnow().strftime('%H:%M:%S')} UTC")
    last_row = get_last_logged_row()
    values = await asyncio.to_thread(get_sheet_values, WATCH_SHEET)
    if not values or len(values) <= last_row:
        return
    headers, data_rows = values[0], values[1:]
    new_rows = data_rows[last_row:]
    new_rows = [row for row in new_rows if any(cell.strip() for cell in row if cell)]
    if not new_rows:
        return

    channel = bot.get_channel(LOGS_CHANNEL_ID)
    if not channel:
        return

    await send_log_rows(channel, new_rows)
    save_last_logged_row(len(values))
    print(f"✅ Posted {len(new_rows)} new rows")

# ---------- EVENTS ----------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    if not daily_stats_task.is_running(): daily_stats_task.start()
    if not sheet_watch_task.is_running(): sheet_watch_task.start()
    await bot.tree.sync()

# ---------- RUN BOT ----------
bot.run(DISCORD_TOKEN)
