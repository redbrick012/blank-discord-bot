
import os
import discord
from discord.ext import tasks, commands
from datetime import datetime, time, timedelta
import asyncio

from sheets import get_daily_stats, get_row_count, get_sheet_values, WATCH_SHEET, STATS_SHEET

# --- Environment Variables ---
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
STATS_CHANNEL_ID = int(os.environ["STATS_CHANNEL_ID"])
LOGS_CHANNEL_ID = int(os.environ["LOGS_CHANNEL_ID"])

# --- Discord Setup ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)  # Use commands.Bot for discord.py

# --- Track last known rows for logs sheet ---
last_known_rows = 0

# --- Embed builder ---
def build_daily_stats_embed(rows, total):
    yesterday = datetime.now() - timedelta(days=1)

    # Function to convert header text to bold-looking Unicode
    def bold_text(text):
        bold_map = str.maketrans(
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
            "𝗔𝗕𝗖𝗗𝗘𝗙𝗚𝗛𝗜𝗝𝗞𝗟𝗠𝗡𝗢𝗣𝗤𝗥𝗦𝗧𝗨𝗩𝗪𝗫𝗬𝗭"
            "𝗮𝗯𝗰𝗱𝗲𝗳𝗴𝗵𝗶𝗷𝗸𝗹𝗺𝗻𝗼𝗽𝗾𝗿𝘀𝘁𝘂𝘷𝘄𝘅𝘆𝘇"
        )
        return text.translate(bold_map)

    # Prepare table
    lines = []
    lines.append("```")
    lines.append(f"{bold_text('Person'):<15} | {bold_text('Items Sent'):>10}")
    lines.append("═" * 28)

    for person, count in rows:
        lines.append(f"{person:<15} | {count:>10}")

    lines.append("═" * 28)
    lines.append(f"💰 {bold_text('Total Sent'):<13} | {total:>10}")
    lines.append("```")

    table = "\n".join(lines)

    embed = discord.Embed(
        title=f"📅 Daily Stats – {yesterday.strftime('%A, %d %B %Y')}",
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=bot.user.display_avatar.url)

    embed.add_field(
        name="Daily Breakdown",
        value=table,
        inline=False
    )

    return embed

def build_log_table(headers, rows):
    lines = []
    lines.append("```")

    header_row = " | ".join(
        headers[col] if col < len(headers) else f"Col {col+1}"
        for col in WATCH_COLUMNS
    )
    lines.append(header_row)
    lines.append("─" * len(header_row))

    for row in rows:
        values = []
        for col in WATCH_COLUMNS:
            values.append(row[col] if col < len(row) and row[col] else "—")
        lines.append(" | ".join(values))

    lines.append("```")
    return "\n".join(lines)


# --- Slash command using @bot.tree.command() ---
@bot.tree.command(name="dailystats", description="Show today's daily stats")
async def dailystats(interaction: discord.Interaction):

    await interaction.response.defer()  # ✅ THIS LINE FIXES 10015

    rows, total = get_daily_stats()
    embed = build_daily_stats_embed(rows, total)
    embed.set_thumbnail(url=bot.user.display_avatar.url)
    
    await interaction.followup.send(embed=embed)

@bot.tree.command(name="lastlog", description="Show log entries from the last hour")
async def lastlog(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    values = get_sheet_values(WATCH_SHEET)

    if not values or len(values) < 2:
        await interaction.followup.send(
            "No log entries found.",
            ephemeral=True
        )
        return

    headers = values[0]
    data_rows = values[1:]

    # Rows added since last hourly check
    start_index = max(0, last_known_rows - 1)
    recent_rows = data_rows[start_index:]

    # Remove empty rows
    recent_rows = [
        row for row in recent_rows
        if any(cell.strip() for cell in row if cell)
    ]
    if not recent_rows:
        # Fallback: show last 10 non-empty rows
        fallback_rows = [
            row for row in reversed(data_rows)
            if any(cell.strip() for cell in row if cell)
        ][:10]
    
        if not fallback_rows:
            await interaction.followup.send(
                "No log entries found.",
                ephemeral=True
            )
            return
    
        fallback_rows.reverse()  # restore chronological order
        table = build_log_table(headers, fallback_rows)
    
        embed = discord.Embed(
            title="🕐 Log Entries (Last 10)",
            description="No new entries in the last hour — showing most recent logs.",
            color=discord.Color.dark_orange(),
            timestamp=datetime.utcnow()
        )

    embed.set_thumbnail(url=bot.user.display_avatar.url)

    embed.add_field(
        name="Last 10 Entries",
        value=table,
        inline=False
    )

    await interaction.followup.send(embed=embed, ephemeral=True)
    return



    table = build_log_table(headers, recent_rows)

    embed = discord.Embed(
        title="🕐 Log Entries (Last Hour)",
        color=discord.Color.orange(),
        timestamp=datetime.utcnow()
    )

    embed.set_thumbnail(url=bot.user.display_avatar.url)

    embed.add_field(
        name=f"{len(recent_rows)} entr{'y' if len(recent_rows) == 1 else 'ies'}",
        value=table,
        inline=False
    )

    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="debugsheet", description="Debug: show last 10 raw rows")
async def debugsheet(interaction: discord.Interaction):
    values = get_sheet_values(WATCH_SHEET)

    if not values:
        await interaction.response.send_message(
            "❌ get_sheet_values returned NOTHING",
            ephemeral=True
        )
        return

    last_rows = values[-10:]
    text = "\n".join(str(row) for row in last_rows)

    await interaction.response.send_message(
        f"Rows seen: {len(values)}\n```{text}```",
        ephemeral=True
    )

# --- Daily stats task at 9 AM ---
@tasks.loop(time=time(hour=9, minute=0, second=0))
async def daily_stats_task():
    channel = bot.get_channel(STATS_CHANNEL_ID)
    if not channel:
        print("Stats channel not found.")
        return
    rows, total = get_daily_stats()
    embed = build_daily_stats_embed(rows, total)
    await channel.send(embed=embed)

# --- Sheet watcher task ---
WATCH_COLUMNS = [0, 1, 2, 4, 5]  # A, B, C, E, F

@tasks.loop(hours=1)
async def sheet_watch_task():
    global last_known_rows

    print("🕐 Hourly sheet_watch_task tick")

    values = get_sheet_values(WATCH_SHEET)

    # Need header + at least one row
    if not values or len(values) < 2:
        return

    headers = values[0]
    current_rows = len(values)

    # Nothing new
    if current_rows <= last_known_rows:
        return

    channel = bot.get_channel(LOGS_CHANNEL_ID)
    if not channel:
        return

    # Rows added since last check
    new_rows = values[last_known_rows:current_rows]

    # Build table
    table_lines = []
    table_lines.append("```")
    
    # Header row
    header_row = " | ".join(
        headers[col] if col < len(headers) else f"Col {col+1}"
        for col in WATCH_COLUMNS
    )
    table_lines.append(header_row)
    table_lines.append("─" * len(header_row))

    entry_count = 0

    for row in new_rows:
        if not any(cell.strip() for cell in row if cell):
            continue

        entry_count += 1

        row_values = []
        for col in WATCH_COLUMNS:
            if col < len(row) and row[col]:
                row_values.append(row[col])
            else:
                row_values.append("—")

        table_lines.append(" | ".join(row_values))

    table_lines.append("```")

    if entry_count == 0:
        last_known_rows = current_rows
        return

    embed = discord.Embed(
        title="🆕 New Log Entries (Last Hour)",
        description="\n".join(table_lines),
        color=discord.Color.orange(),
        timestamp=datetime.utcnow()
    )

    embed.set_footer(
        text=f"{entry_count} new entr{'y' if entry_count == 1 else 'ies'} added"
    )

    await channel.send(embed=embed)

    last_known_rows = current_rows


# --- Events ---
@bot.event
async def on_ready():
    global last_known_rows

    print(f"✅ Logged in as {bot.user}")

    # Initialize last known rows
    last_known_rows = get_row_count(WATCH_SHEET)

    # Start background tasks safely
    if not daily_stats_task.is_running():
        daily_stats_task.start()

    if not sheet_watch_task.is_running():
        sheet_watch_task.start()

    # Sync slash commands
    await bot.tree.sync()

# --- Run bot ---
bot.run(DISCORD_TOKEN)
