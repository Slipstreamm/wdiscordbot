import os
import shutil
import subprocess
import sys
import discord
from discord.ext import commands
from discord import app_commands

class GitUpdateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="update", description="Updates the bot code from GitLab and restarts the bot. (Admin Only)")
    async def update(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to run this command.", ephemeral=True)
            return
        message = await interaction.response.send_message("Initiating update. The bot will restart shortly...")
        target_dir = "/home/server/wdiscordbotserver/"
        repo_url = "https://gitlab.com/pancakes1234/wdiscordbotserver.git"
        restart_script = "/home/server/wdiscordbotserver/bot.py"

        try:
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
                await message.edit(content=f"Removed directory: {target_dir}")
            else:
                await message.edit(content=f"Directory {target_dir} does not exist; proceeding with clone...")
            subprocess.run(["git", "clone", repo_url, target_dir], check=True)
            await message.edit(content="Repository cloned successfully.")
        except Exception as e:
            error_msg = f"Update failed: {e}"
            print(error_msg)
            await message.edit(content=error_msg)
            return
        try:
            await message.edit(content="Bot has updated to the latest commit and is restarting...")
            os.execv(sys.executable, [sys.executable, restart_script])
            # If os.execv returns, it means it failed
        except Exception as e:
            await message.edit(content=f"Failed to restart bot: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(GitUpdateCog(bot))
