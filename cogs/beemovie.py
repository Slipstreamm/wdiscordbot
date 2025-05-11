import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

class BeeMovie(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="beemovie",
        description="Fetches and displays the Bee Movie script from the API."
    )
    async def beemovie(self, interaction: discord.Interaction):
        # The API endpoint URL
        url = "https://api.database.learnhelp.cc/database/beemoviescript.json"
        
        # Fetch the JSON from the API
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    script_text = data.get("script")

                    if script_text is None:
                        await interaction.response.send_message(
                            "The API response did not include a 'script' field.",
                            ephemeral=True
                        )
                        return
                    
                    # If the script is too long for a single Discord message,
                    # we split it into smaller chunks.
                    if len(script_text) > 1900:
                        await interaction.response.send_message(
                            "The Bee Movie script is too long; here it is in parts:"
                        )
                        parts = [script_text[i:i+1900] for i in range(0, len(script_text), 1900)]
                        for part in parts:
                            await interaction.followup.send(part)
                    else:
                        await interaction.response.send_message(script_text)
                else:
                    await interaction.response.send_message(
                        f"Failed to fetch the script. HTTP error: {response.status}",
                        ephemeral=True
                    )

# This setup function is used to load the cog with app_commands.
async def setup(bot: commands.Bot):
    await bot.add_cog(BeeMovie(bot))