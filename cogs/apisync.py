import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
from datetime import datetime

class BotGitlabNewsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Set launch time on first load for uptime calculations.
        if not hasattr(bot, "launch_time"):
            bot.launch_time = datetime.utcnow()
        # Create or reuse a dictionary to track command usage.
        if not hasattr(bot, "command_usage"):
            bot.command_usage = {}

    async def _update_usage(self, command: str) -> None:
        """Helper method to update the usage counter for a given command."""
        self.bot.command_usage[command] = self.bot.command_usage.get(command, 0) + 1

    @app_commands.command(name="botnews", description="Displays the latest bot news live from GitLab with updated commit statistics.")
    async def botnews(self, interaction: discord.Interaction) -> None:
        await self._update_usage("botnews")
        # GitLab repository details:
        # Git clone URL: https://gitlab.com/pancakes1234/wdiscordbotserver.git
        # Project ID is 69642305 and project_path is used to build the commit URL.
        project_id = "69642305"
        project_path = "pancakes1234/wdiscordbotserver"

        # API endpoint to fetch the latest commit (1 commit) with statistics.
        url = f"https://gitlab.com/api/v4/projects/{project_id}/repository/commits?per_page=1&stats=true"

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    commits = await resp.json()
                    if commits:
                        latest_commit = commits[0]
                        commit_title    = latest_commit.get("title", "No Title")
                        commit_message  = latest_commit.get("message", "No Message")
                        commit_id       = latest_commit.get("id", "N/A")
                        commit_date_str = latest_commit.get("committed_date", None)
                        
                        # Format the commit date.
                        if commit_date_str and commit_date_str.endswith("Z"):
                            commit_date_str = commit_date_str.replace("Z", "+00:00")
                        try:
                            commit_date = datetime.fromisoformat(commit_date_str) if commit_date_str else datetime.utcnow()
                        except Exception:
                            commit_date = datetime.utcnow()
                        formatted_date = commit_date.strftime("%Y-%m-%d %H:%M:%S UTC")
                        
                        # Create a URL to view the commit on GitLab.
                        commit_url = f"https://gitlab.com/{project_path}/-/commit/{commit_id}"
                        
                        embed = discord.Embed(
                            title="Bot News - Latest GitLab Commit",
                            description=f"**{commit_title}**\n\n{commit_message}",
                            url=commit_url,
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="Commit ID", value=commit_id[:8], inline=True)
                        embed.add_field(name="Date", value=formatted_date, inline=True)
                        
                        # If commit statistics exist, add them.
                        commit_stats = latest_commit.get("stats", {})
                        if commit_stats:
                            additions    = commit_stats.get("additions", 0)
                            deletions    = commit_stats.get("deletions", 0)
                            total_change = commit_stats.get("total", 0)
                            
                            embed.add_field(name="Additions", value=str(additions), inline=True)
                            embed.add_field(name="Deletions", value=str(deletions), inline=True)
                            embed.add_field(name="Total Changes", value=str(total_change), inline=True)
                        
                        embed.set_footer(text="Live update from GitLab")
                        await interaction.response.send_message(embed=embed)
                    else:
                        await interaction.response.send_message("No commits found in the specified repository.", ephemeral=True)
                else:
                    await interaction.response.send_message("Failed to retrieve data from GitLab.", ephemeral=True)

    @app_commands.command(name="increment", description="Increments a counter on the API and returns its updated value.")
    async def increment(self, interaction: discord.Interaction) -> None:
        await self._update_usage("increment")
        url = "https://api.learnhelp.cc/discord/increment.json/"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    counter_val = data.get("counter", "unknown")
                    timestamp = data.get("timestamp", "")
                    
                    embed = discord.Embed(
                        title="Increment Counter",
                        description=f"Counter is now: **{counter_val}**",
                        color=discord.Color.purple()
                    )
                    embed.set_footer(text=f"Timestamp: {timestamp}")
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message("Failed to increment counter.", ephemeral=True)

    @app_commands.command(name="botmetrics", description="Displays real-time metrics from the live bot instance.")
    async def botmetrics(self, interaction: discord.Interaction) -> None:
        await self._update_usage("botmetrics")
        now = datetime.utcnow()
        # Calculate uptime from the bot's launch time.
        uptime_timedelta = now - self.bot.launch_time
        uptime_seconds = int(uptime_timedelta.total_seconds())
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        server_count = len(self.bot.guilds)
        latency_ms = round(self.bot.latency * 1000, 2)
        
        # Retrieve live usage statistics from the bot.
        command_usage = self.bot.command_usage
        # Construct the usage lines for each command we track.
        usage_lines = "\n".join(f"`{cmd}`: {count}" for cmd, count in command_usage.items())

        embed = discord.Embed(
            title="Bot Metrics",
            description="Real-time statistics of the bot",
            color=discord.Color.green()
        )
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        embed.add_field(name="Server Count", value=str(server_count), inline=True)
        embed.add_field(name="Latency", value=f"{latency_ms}ms", inline=True)
        embed.add_field(name="Command Usage", value=usage_lines or "No data", inline=False)
        embed.set_footer(text=f"Timestamp: {now.isoformat()}Z")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BotGitlabNewsCog(bot))
