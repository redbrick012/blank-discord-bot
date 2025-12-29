import os
import discord
from discord.ext import commands

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # Sync slash commands with Discord
    await bot.tree.sync()
    print(f"Logged in as {bot.user} (slash commands synced)")

@bot.tree.command(name="ping", description="Replies with Pong!")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

bot.run(os.getenv("DISCORD_TOKEN"))


from sheets import get_sheet_data

SPREADSHEET_ID = "YOUR_SPREADSHEET_ID"

@bot.tree.command(name="sheet")
async def sheet(interaction: discord.Interaction):
    data = get_sheet_data(SPREADSHEET_ID, "Sheet1")

    if not data:
        await interaction.response.send_message("No data found.")
        return

    first_row = data[0]
    await interaction.response.send_message(f"First row:\n{first_row}")
