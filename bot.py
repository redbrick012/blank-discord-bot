
#SPREADSHEET_ID = "1HKZ_4m-U-9r3Tqdzn98Ztul7XkifyU9Pn2t_ur8QW8I"

import os
import discord
from discord.ext import commands
from sheets import get_sheet_data

# Google Sheet ID (replace with your own)
SPREADSHEET_ID = "YOUR_SPREADSHEET_ID_HERE"
WORKSHEET_NAME = "Daily Stats"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ----- SLASH COMMANDS -----

@bot.tree.command(name="ping", description="Replies with Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

@bot.tree.command(name="sheet", description="Shows first row of Daily Stats")
async def sheet(interaction: discord.Interaction):
    data = get_sheet_data(SPREADSHEET_ID, WORKSHEET_NAME)

    if not data:
        await interaction.response.send_message("No data found or error reading sheet.")
        return

    # Send first row as a readable string
    first_row = data[0]
    formatted = "\n".join(f"{k}: {v}" for k, v in first_row.items())
    await interaction.response.send_message(f"First row:\n{formatted}")

# ----- EVENTS -----

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (slash commands synced)")

bot.run(os.getenv("DISCORD_TOKEN"))

@bot.tree.command(name="sheetrange", description="Shows a specific range from the sheet")
async def sheetrange(interaction: discord.Interaction):
    # Example: B4:C12
    cell_range = "B4:C12"
    data = get_sheet_data(SPREADSHEET_ID, WORKSHEET_NAME, cell_range)

    if not data:
        await interaction.response.send_message("No data found or error reading sheet.")
        return

    # Format nicely as a table
    formatted = ""
    for row in data:
        formatted += " | ".join(str(cell) for cell in row) + "\n"

    # Discord messages have a limit; use code block for table formatting
    await interaction.response.send_message(f"```\n{formatted}```")
