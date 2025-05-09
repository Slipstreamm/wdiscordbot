import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import urllib.parse

# A view with a button to display commit diffs.
class DiffView(discord.ui.View):
    def __init__(self, diffs):
        super().__init__(timeout=60)  # Button active for 60 seconds.
        self.diffs = diffs

    @discord.ui.button(label="Show Diffs", style=discord.ButtonStyle.primary)
    async def show_diffs(self, button: discord.ui.Button, interaction: discord.Interaction):
        diff_message = ""
        # Format each file's diff info.
        for diff in self.diffs:
            file_path = diff.get("new_path", "Unknown file")
            diff_text = diff.get("diff", "No diff available")
            diff_message += f"**File:** {file_path}\n```diff\n{diff_text}\n```\n"
        # Truncate if too long.
        if len(diff_message) > 1900:
            diff_message = diff_message[:1900] + "\n...[truncated]"
        await interaction.response.send_message(diff_message, ephemeral=True)

# The cog defining the /changes command.
class GitlabChanges(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.repo = "pancakes1234/wdiscordbotserver"
        # URL-encode the repository identifier for the GitLab API.
        self.project_id = urllib.parse.quote_plus(self.repo)

    @app_commands.command(
        name="changes",
        description="Display details of the latest commit for the bot"
    )
    async def changes(self, interaction: discord.Interaction):
        # Defer the response to allow for asynchronous API calls.
        await interaction.response.defer()
        
        # Fetch the list of commits via GitLab's API.
        async with aiohttp.ClientSession() as session:
            commits_url = f"https://gitlab.com/api/v4/projects/{self.project_id}/repository/commits"
            async with session.get(commits_url) as resp:
                if resp.status != 200:
                    await interaction.followup.send("Failed to fetch commits from GitLab.")
                    return
                commits = await resp.json()

        if not commits:
            await interaction.followup.send("No commits found.")
            return

        # Retrieve the most recent commit.
        latest_commit = commits[0]
        commit_hash = latest_commit.get("id", "N/A")
        commit_message = latest_commit.get("message", "No commit message provided.")
        author_name = latest_commit.get("author_name", "Unknown author")
        # Construct a clickable link for the commit.
        commit_url = f"https://gitlab.com/{self.repo}/-/commit/{commit_hash}"

        # Fetch diff details for the commit.
        async with aiohttp.ClientSession() as session:
            diff_url = f"https://gitlab.com/api/v4/projects/{self.project_id}/repository/commits/{commit_hash}/diff"
            async with session.get(diff_url) as diff_resp:
                if diff_resp.status != 200:
                    diffs = []
                    files_field = "Could not fetch diff details."
                else:
                    diffs = await diff_resp.json()
                    file_list = [diff.get("new_path", "Unknown file") for diff in diffs]
                    files_field = "\n".join(file_list) if file_list else "No files changed."

        # Build the embed with commit details.
        embed = discord.Embed(
            title="Latest Commit",
            description=f"Latest commit from **{self.repo}**",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Commit Hash", value=commit_hash, inline=False)
        embed.add_field(name="Author", value=author_name, inline=False)
        embed.add_field(name="Description", value=commit_message, inline=False)
        embed.add_field(name="Files Edited", value=files_field, inline=False)
        embed.add_field(name="Commit Link", value=f"[View Commit]({commit_url})", inline=False)

        # Attach the diff button view so the user can check diffs on demand.
        view = DiffView(diffs)
        await interaction.followup.send(embed=embed, view=view)

# Standard setup function for loading the cog.
async def setup(bot: commands.Bot):
    await bot.add_cog(GitlabChanges(bot))
