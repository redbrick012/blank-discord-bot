import asyncio
from datetime import datetime
import discord
from discord.ext import tasks
from discord.errors import NotFound

class StockManager:
    def __init__(self, bot, get_sheet_values):
        """
        bot: your discord.Bot or commands.Bot instance
        get_sheet_values: function to fetch rows from Google Sheets
        """
        self.bot = bot
        self.get_sheet_values = get_sheet_values
        self.tasks = {}  # keep track of active stock tasks by channel

    async def fetch_inventory_sorted(self, stock_sheet, priority_sheet):
        """Fetch inventory and reorder by priority first, then Scarcity Rating descending."""
        inventory = await asyncio.to_thread(self.get_sheet_values, stock_sheet)
        priority = await asyncio.to_thread(self.get_sheet_values, priority_sheet)

        if not inventory or len(inventory) < 2:
            return [], []

        headers = inventory[0]
        rows = inventory[1:]

        # Build priority map {Item Name: Priority Rank}
        priority_map = {}
        if priority and len(priority) > 1:
            for row in priority[1:]:
                if len(row) > 1 and row[1]:
                    priority_map[row[1]] = int(row[0])

        # Add priority rank to each row
        for row in rows:
            item = row[0]
            row.append(priority_map.get(item, 999))

        # Sort: priority first, then Scarcity Rating descending
        def sort_key(r):
            scarcity = int(r[5]) if len(r) > 5 and str(r[5]).isdigit() else 0
            priority_rank = r[-1]
            return (priority_rank, -scarcity)

        rows.sort(key=sort_key)

        # Remove added sort column before displaying
        for row in rows:
            row.pop(-1)

        return headers, rows

   def build_stock_table(self, headers, rows, stock_columns=[0,1,2,3,4,5]):
    """Return a nicely aligned code-block table for Discord embed."""
    table_rows = [[row[i] if i < len(row) and row[i] else "—" for i in stock_columns] for row in rows]

    # Column widths
    col_widths = []
    for i, col in enumerate(stock_columns):
        max_width = len(headers[col]) if col < len(headers) else len(f"Col {col+1}")
        for row in table_rows:
            max_width = max(max_width, len(str(row[i])))
        col_widths.append(max_width)

    # Header + separator
    header_line = " | ".join(
        (headers[col] if col < len(headers) else f"Col {col+1}").ljust(col_widths[i])
        for i, col in enumerate(stock_columns)
    )
    separator_line = "─" * len(header_line)

    # Row lines
    row_lines = []
    for row in table_rows:
        line = " | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(stock_columns)))
        row_lines.append(line)

    return "```\n" + header_line + "\n" + separator_line + "\n" + "\n".join(row_lines) + "\n```"
