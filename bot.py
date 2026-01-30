import os
import discord
from discord.ext import commands, tasks

from sheets import (
    get_last_processed_row,
    save_last_processed_row,
    get_new_log_rows
)

# =====================
# ENVIRONMENT VARIABLES
# =====================
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = 1455538936683434024
LOGS_CHANNEL_ID = int(os.getenv("LOGS_CHANNEL_ID", 0))

# =====================
# DISCORD SETUP
# =====================
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# =====================
# EVENTS
# =====================
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    sheet_watch_task.start()


# =====================
# EMBED BUILDER
# =====================
def build_log_embeded(rows):
    """
    Builds one or more embeds, automatically splitting
    if Discord's 6000 character limit is approached.
    """
    embeds = []
    current_description = ""

    for row in rows:
        # Defensive check
        if len(row) < 8:
            continue

        # Adjust indexes here if your sheet columns differ
        timestamp = row[0]
        category = row[1]
        title = row[2]
        item = row[4]
        qty = row[5]
        author = row[7]

        line = (
            f"**[{author}]** {title}\n"
            f"• {item} ×{qty}\n"
            f"• {timestamp}\n\n"
        )

        # If adding this line would exceed Discord limits
        if len(current_description) + len(line) > 5500:
            embed = discord.Embed(
                title="📦 New Log Entries",
                description=current_description,
                color=0x2ecc71
            )
            embeds.append(embed)
            current_description = ""

        current_description += line

    if current_description:
        embed = discord.Embed(
            title="📦 New Log Entries",
            description=current_description,
            color=0x2ecc71
        )
        embeds.append(embed)

    return embeds


# =====================
# BACKGROUND TASK
# =====================
@tasks.loop(minutes=15)
async def sheet_watch_task():
    new_rows, current_last_row = get_new_log_rows()

    if not new_rows:
        return

    channel = bot.get_channel(LOGS_CHANNEL_ID)
    if not channel:
        return

    embed = build_log_embed(new_rows)
    await channel.send(embed=embed)

    save_last_processed_row(current_last_row)
    print(f"✅ Posted {len(new_rows)} new rows")


# =====================
# START BOT
# =====================
bot.run(DISCORD_TOKEN)
