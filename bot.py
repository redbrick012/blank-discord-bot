
#SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"
#CHANNEL_ID = 1455146969579126951

import discord
from discord.ext import commands, tasks
from sheets import get_daily_stats, get_row_count
import os

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

STATS_CHANNEL_ID = int(os.environ["STATS_CHANNEL_ID"])
WATCH_SHEET = "Logs"  # 👈 tab to monitor

last_known_rows = 0

# -------------------------
# READY
# -------------------------
@bot.event
async def on_ready():
    global last_known_rows

    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

    last_known_rows = get_row_count(WATCH_SHEET)

    daily_stats_task.start()
    sheet_watch_task.start()

# -------------------------
# EMBED BUILDER
# -------------------------
def build_daily_stats_embed(rows, total):
    embed = discord.Embed(
        title="📅 Daily Stats",
        color=discord.Color.dark_teal()
    )

    # Build two columns as inline fields
    names_column = "\n".join(name for name, _ in rows)
    values_column = "\n".join(str(value) for _, value in rows)

    embed.add_field(
        name="Person",
        value=names_column or "No data",
        inline=True
    )

    embed.add_field(
        name="Items Sent",
        value=values_column or "No data",
        inline=True
    )

    # Total as a separate full-width field
    embed.add_field(
        name="Total Sent",
        value=f"**{total}**",
        inline=False
    )

    return embed

# -------------------------
# SLASH COMMAND
# -------------------------
@bot.tree.command(name="dailystats", description="Show today's stats")
async def dailystats(interaction: discord.Interaction):
    await interaction.response.defer()

    rows, total = get_daily_stats()
    embed = build_daily_stats_embed(rows, total)

    await interaction.followup.send(embed=embed)

# -------------------------
# DAILY AUTO POST (9am UTC)
# -------------------------
@tasks.loop(hours=24)
async def daily_stats_task():
    channel = bot.get_channel(STATS_CHANNEL_ID)

    rows, total = get_daily_stats()
    embed = build_daily_stats_embed(rows, total)

    await channel.send(embed=embed)

@daily_stats_task.before_loop
async def before_daily_stats():
    await bot.wait_until_ready()

# -------------------------
# NEW ROW DETECTOR (polling)
# -------------------------
@tasks.loop(minutes=2)
async def sheet_watch_task():
    global last_known_rows

    current_rows = get_row_count(WATCH_SHEET)

    if current_rows > last_known_rows:
        channel = bot.get_channel(STATS_CHANNEL_ID)
        await channel.send(
            f"🆕 **New entry added to `{WATCH_SHEET}`**\n"
            f"Rows: `{last_known_rows} → {current_rows}`"
        )
        last_known_rows = current_rows

@sheet_watch_task.before_loop
async def before_sheet_watch():
    await bot.wait_until_ready()

# -------------------------
bot.run(os.environ["DISCORD_TOKEN"])
