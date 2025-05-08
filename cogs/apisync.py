import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

class MetricsCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    metrics_group = app_commands.Group(name="metrics", description="Access various bot metrics")

    @metrics_group.command(
        name="local",
        description="Display live bot metrics (calculated locally)."
    )
    async def local_metrics(self, interaction: discord.Interaction) -> None:
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

        # Format the metrics for local display.
        metrics_output = "Live Bot Metrics:\n"
        metrics_output += f"Uptime: {metrics_data['uptime']}\n"
        metrics_output += f"Server Count: {metrics_data['server_count']}\n"
        metrics_output += f"Latency: {metrics_data['latency']}\n"
        metrics_output += "Command Usage:\n"
        if metrics_data['command_usage']:
            for command, count in metrics_data['command_usage'].items():
                metrics_output += f"  {command}: {count}\n"
        else:
            metrics_output += "  No command usage recorded yet.\n"
        metrics_output += f"Timestamp: {metrics_data['timestamp']}"

        # Send the metrics locally.
        await interaction.response.send_message(metrics_output, ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MetricsCog(bot))
