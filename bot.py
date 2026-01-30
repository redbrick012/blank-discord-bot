from discord.ext import commands, tasks
import discord

from sheets import (
    get_last_processed_row,
    set_last_processed_row,
    get_new_log_rows
)

CHANNEL_ID = int(os.environ["INVENTORY_CHANNEL_ID"])

bot = commands.Bot(command_prefix="!", intents=discord.Intents.default())


@bot.event
async def on_ready():
    sheet_watch_task.start()
    print("Bot online")


def build_log_embed(rows):
    embed = discord.Embed(
        title="📦 New Inventory Logs",
        color=0x2ecc71
    )

    description = ""
    for row in rows:
        description += (
            f"**{row[7]}** • {row[4]} | QTY: {row[5]}\n"
            if len(row) > 7 else "Malformed row\n"
        )

    embed.description = description[:5900]
    return embed


@tasks.loop(minutes=1)
async def sheet_watch_task():
    channel = bot.get_channel(CHANNEL_ID)

    last_row = get_last_processed_row()
    new_rows, current_last_row = get_new_log_rows(last_row)

    if not new_rows:
        return  # ✅ NOTHING NEW → DO NOTHING

    await channel.send(embed=build_log_embed(new_rows))

    # ✅ Update state ONLY after successful send
    set_last_processed_row(current_last_row)
