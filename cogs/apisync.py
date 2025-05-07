import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import os
from datetime import datetime

class ApiPushMetricsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="pushmetrics",
        description="Push live bot metrics to the API."
    )
    async def pushmetrics(self, interaction: discord.Interaction) -> None:
        # Calculate live metrics.
        now = datetime.utcnow()
        uptime_delta = now - self.bot.launch_time
        uptime_seconds = int(uptime_delta.total_seconds())
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        server_count = len(self.bot.guilds)
        latency_ms = round(self.bot.latency * 1000, 2)
        command_usage = getattr(self.bot, "command_usage", {})

        metrics_data = {
            "uptime": uptime_str,
            "server_count": server_count,
            "latency": f"{latency_ms}ms",
            "command_usage": command_usage,
            "timestamp": now.isoformat() + "Z"
        }

        # Get the API key from the environment variable LHAPI_KEY.
        lh_api_key = os.getenv("LHAPI_KEY")
        if not lh_api_key:
            await interaction.response.send_message("Environment variable LHAPI_KEY is not set.", ephemeral=True)
            return

        # The API endpoint URL (adjust if needed).
        url = "https://learnhelpapi.onrender.com/discord/botmetrics.json/"

        headers = {
            "X-API-Key": lh_api_key
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=metrics_data, headers=headers) as resp:
                    if resp.status == 200:
                        await interaction.response.send_message("Successfully pushed live metrics to the API.", ephemeral=True)
                    else:
                        error_text = await resp.text()
                        await interaction.response.send_message(
                            f"Failed to push metrics. Status: {resp.status}. Error: {error_text}",
                            ephemeral=True
                        )
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ApiPushMetricsCog(bot))
