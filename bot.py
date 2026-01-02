
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

# --- Helper: build a perfectly aligned table ---
def build_log_table(headers, rows):
    # Calculate max width per column
    col_widths = []
    for i, col in enumerate(WATCH_COLUMNS):
        # Header width
        header_text = headers[col] if col < len(headers) else f"Col {col+1}"
        max_width = len(header_text)
        # Cell widths
        for row in rows:
            if col < len(row) and row[col]:
                max_width = max(max_width, len(row[col]))
        col_widths.append(max_width)

    # Build header line
    header_line = " | ".join(
        (headers[col] if col < len(headers) else f"Col {col+1}").ljust(col_widths[i])
        for i, col in enumerate(WATCH_COLUMNS)
    )

    # Separator
    separator_line = "─" * len(header_line)

    # Build row lines
    row_lines = []
    for row in rows:
        line = " | ".join(
            (row[col] if col < len(row) and row[col] else "—").ljust(col_widths[i])
            for i, col in enumerate(WATCH_COLUMNS)
        )
        row_lines.append(line)

    table = "```\n" + header_line + "\n" + separator_line + "\n" + "\n".join(row_lines) + "\n```"
    return table



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
    await interaction.response.defer()  # public response

    # Fetch sheet values without blocking
    values = await asyncio.to_thread(get_sheet_values, WATCH_SHEET)

    if not values or len(values) < 2:
        await interaction.followup.send("No log entries found.")
        return

    headers = values[0]
    data_rows = values[1:]

    # Only last 100 rows for speed
    recent_data = data_rows[-100:]

    # Rows added since last known row
    start_index = max(0, last_known_rows - 1)
    new_rows = recent_data[start_index:]
    new_rows = [r for r in new_rows if any(cell.strip() for cell in r if cell)]

    # Fallback: show last 10 rows if nothing new
    if not new_rows:
        fallback_rows = [r for r in reversed(recent_data) if any(cell.strip() for cell in r if cell)][:10]
        fallback_rows.reverse()

        if not fallback_rows:
            await interaction.followup.send("No log entries found.")
            return

        new_rows = fallback_rows

    # Build one embed per row
    embeds = []
    for row in new_rows:
        embed = discord.Embed(
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        
        for i, col in enumerate(WATCH_COLUMNS):
            col_name = headers[col] if col < len(headers) else f"Col {col+1}"
            col_value = row[col] if col < len(row) and row[col] else "—"
            embed.add_field(name=col_name, value=col_value, inline=True)

        embeds.append(embed)

    # Discord limits 10 embeds per message
    for i in range(0, len(embeds), 10):
        await interaction.followup.send(embeds=embeds[i:i+10])


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

@bot.tree.command(name="loghour", description="Show testing log for the last hour")
async def loghour(interaction: discord.Interaction):
    await interaction.response.defer()  # make it ephemeral if needed

    # Fetch all rows from the watch sheet
    values = await asyncio.to_thread(get_sheet_values, WATCH_SHEET)
    if not values or len(values) < 2:
        await interaction.followup.send("No log entries found.")
        return

    headers = values[0]
    data_rows = values[1:]

    # Filter rows from the last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_rows = []

    for row in data_rows:
        try:
            # Attempt to parse timestamp from column 0 (A)
            time_cell = row[0] if len(row) > 0 else None
            if time_cell:
                row_time = datetime.strptime(time_cell, "%d/%m/%Y %H:%M:%S")  # adjust format to your sheet
            else:
                row_time = datetime.utcnow()

            if row_time >= one_hour_ago:
                recent_rows.append(row)
        except Exception:
            # fallback: include row if timestamp invalid
            recent_rows.append(row)

    if not recent_rows:
        await interaction.followup.send("No log entries in the last hour.")
        return

    # Build log lines
    log_lines = []
    for row in recent_rows:
        name = row[7] if len(row) > 7 else "Unknown"
        method = row[2] if len(row) > 2 else "—"
        qty = row[5] if len(row) > 5 else "0"
        item = row[4] if len(row) > 4 else "—"
        time_str = row[0] if len(row) > 0 else datetime.utcnow().strftime("%H:%M:%S")

        log_lines.append(f"[{name}]: {method} - {qty} x {item} at {time_str}")

    # Send in chunks to avoid Discord 2000-char limit
    chunk_size = 1900
    current_chunk = ""
    for line in log_lines:
        if len(current_chunk) + len(line) + 1 > chunk_size:
            await interaction.followup.send(f"```{current_chunk}```")
            current_chunk = ""
        current_chunk += line + "\n"

    if current_chunk:
        await interaction.followup.send(f"```{current_chunk}```")


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

@tasks.loop(minutes=60)  # runs every 60 minutes
async def sheet_watch_task():
    """Check the watch sheet every hour and post new rows as individual embeds."""
    global last_known_rows

    print(f"🕐 sheet_watch_task tick at {datetime.utcnow().strftime('%H:%M:%S')} UTC")

    # Fetch sheet values without blocking
    values = await asyncio.to_thread(get_sheet_values, WATCH_SHEET)
    if not values or len(values) < 2:
        return

    headers = values[0]
    current_rows = len(values)

    # Nothing new
    if current_rows <= last_known_rows:
        return

    channel = bot.get_channel(LOGS_CHANNEL_ID)
    if not channel:
        print("Logs channel not found.")
        return

    # Rows added since last check
    new_rows = values[last_known_rows:current_rows]
    new_rows = [row for row in new_rows if any(cell.strip() for cell in row if cell)]

    if not new_rows:
        last_known_rows = current_rows
        return

    # Build one embed per new row
    embeds = []
    for row in new_rows:
        embed = discord.Embed(
            title="🆕 New Log Entry",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        embed.set_thumbnail(url=bot.user.display_avatar.url)

        for i, col in enumerate(WATCH_COLUMNS):
            col_name = headers[col] if col < len(headers) else f"Col {col+1}"
            col_value = row[col] if col < len(row) and row[col] else "—"
            embed.add_field(name=col_name, value=col_value, inline=True)

        embeds.append(embed)

    # Discord limit: max 10 embeds per message
    for i in range(0, len(embeds), 10):
        await channel.send(embeds=embeds[i:i+10])

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
