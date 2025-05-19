import discord
from discord.ext import commands
from discord import app_commands
import os

class TerminalOutput(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.log_file_path = 'bot.log'

    @app_commands.command(name='logs', description='Shows the bot log output (Admin only)')
    @app_commands.has_permissions(administrator=True) # Restrict to bot owner, can change to check for admin role if needed
    async def show_logs(self, interaction: discord.Interaction):
        if not os.path.exists(self.log_file_path):
            await interaction.response.send_message("Log file not found.", ephemeral=True)
            return

        try:
            with open(self.log_file_path, 'r') as f:
                log_content = f.read()
        except Exception as e:
            await interaction.response.send_message(f"Error reading log file: {e}", ephemeral=True)
            return

        if not log_content:
            await interaction.response.send_message("Log file is empty.", ephemeral=True)
            return

        # Split output into chunks of less than 2000 characters
        chunks = [log_content[i:i + 1990] for i in range(0, len(log_content), 1990)] # Leave some buffer for formatting

        # Send the first chunk as the initial response
        await interaction.response.send_message(f"```\n{chunks[0]}\n```", ephemeral=True)

        # Send subsequent chunks as followups
        for chunk in chunks[1:]:
            await interaction.followup.send(f"```\n{chunk}\n```", ephemeral=True)


async def setup(bot):
    await bot.add_cog(TerminalOutput(bot))
