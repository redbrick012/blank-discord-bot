import os
import discord
from discord.ext import commands, tasks

from sheets import (
    get_last_processed_row,
    set_last_processed_row,
    get_new_log_rows
)

# =====================
# ENVIRONMENT VARIABLES
# =====================
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["INVENTORY_CHANNEL_ID"])

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
def build_log_embeds(rows):
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
@tasks.loop(minutes=1)
async def sheet_watch_task():
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("❌ Channel not found")
        return

    # 1️⃣ Read last processed row from __STATE!A1
    last_row = get_last_processed_row()

    # 2️⃣ Fetch only rows AFTER that row
    new_rows, current_last_row = get_new_log_rows(last_row)

    # 3️⃣ Nothing new → do nothing
    if not new_rows:
        return

    # 4️⃣ Build embeds safely
    embeds = build_log_embeds(new_rows)

    # 5️⃣ Send embeds
    for embed in embeds:
        await channel.send(embed=embed)

    # 6️⃣ Update __STATUS!A1 ONLY after successful send
    set_last_processed_row(current_last_row)

    print(
        f"📤 Posted {len(new_rows)} new rows "
        f"(rows {last_row + 1} → {current_last_row})"
    )


# =====================
# START BOT
# =====================
bot.run(DISCORD_TOKEN)
