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
