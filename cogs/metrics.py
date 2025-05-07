import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

class MetricsDisplayCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="metrics",
        description="Displays live bot metrics fetched from the API."
    )
    async def metrics(self, interaction: discord.Interaction) -> None:
        # URL of your metrics API endpoint.
        url = "https://api.learnhelp.cc/discord/botmetrics.json/"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()

                    # Extract bot metrics from the API response.
                    uptime = data.get("uptime", "N/A")
                    server_count = data.get("server_count", "N/A")
                    latency = data.get("latency", "N/A")
                    timestamp = data.get("timestamp", "N/A")

                    # Format command usage statistics.
                    command_usage = data.get("command_usage", {})
                    if command_usage:
                        usage_lines = "\n".join(
                            f"**{cmd}**: {count}" for cmd, count in command_usage.items()
                        )
                    else:
                        usage_lines = "N/A"

                    # Create the embed.
                    embed = discord.Embed(
                        title="Live Bot Metrics",
                        description="These metrics are fetched directly from the API.",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Uptime", value=uptime, inline=True)
                    embed.add_field(name="Server Count", value=str(server_count), inline=True)
                    embed.add_field(name="Latency", value=latency, inline=True)
                    embed.add_field(name="Command Usage", value=usage_lines, inline=False)
                    embed.set_footer(text=f"Last Updated: {timestamp}")

                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message(
                        f"Failed to retrieve bot metrics. API returned status: {response.status}",
                        ephemeral=True
                    )

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MetricsDisplayCog(bot))