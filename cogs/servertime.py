import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import time

class ServerTime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="timeis", description="Shows the server's current time and date with timezone.")
    async def timeis(self, interaction: discord.Interaction):
        # Get local time with timezone
        local_time = datetime.now().astimezone()
        timezone_name = time.tzname[local_time.dst() != 0]
        formatted_time = local_time.strftime("%Y-%m-%d %H:%M:%S")
        embed = discord.Embed(
            title="Server Time",
            description=f"**{formatted_time}**\nTimezone: `{timezone_name}`",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerTime(bot))
