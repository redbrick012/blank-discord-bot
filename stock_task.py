# stock_task.py
import asyncio
from datetime import datetime
import discord
from discord.ext import tasks

STOCK_SHEET = "inventory_Flowers"
PRIORITY_SHEET = "priority_Flowers"
STOCK_COLUMNS = [0, 1, 2, 3, 4, 5]

stock_message_id = None

async def fetch_inventory_sorted(get_sheet_values):
    # ... your fetch_inventory_sorted code here
    return headers, rows

def build_stock_table(headers, rows):
    # ... your build_stock_table code here
    return "table string"

def setup_stock_task(bot, get_sheet_values, STOCK_CHANNEL_ID):
    @tasks.loop(minutes=15)
    async def stock_check_task():
        nonlocal stock_message_id
        channel = bot.get_channel(STOCK_CHANNEL_ID)
        if not channel:
            print("Stock channel not found")
            return
        headers, rows = await fetch_inventory_sorted(get_sheet_values)
        if not rows:
            print("No inventory rows found")
            return
        table_text = build_stock_table(headers, rows)
        embed = discord.Embed(
            title="📦 Inventory Status",
            description=table_text,
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Updated every 15 minutes")
        embed.set_thumbnail(url=bot.user.display_avatar.url)

        try:
            if stock_message_id:
                msg = await channel.fetch_message(stock_message_id)
                await msg.edit(embed=embed)
            else:
                msg = await channel.send(embed=embed)
                stock_message_id = msg.id
        except discord.NotFound:
            msg = await channel.send(embed=embed)
            stock_message_id = msg.id

    stock_check_task.start()
