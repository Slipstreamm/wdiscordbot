import discord
from discord.ext import commands
from discord import app_commands
import aiohttp

class TetoImage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="randomtetoimage", description="Gets a random Teto image from slipstreamm.dev")
    async def random_teto_image(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Acknowledge the interaction immediately

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get("https://slipstreamm.dev/teto") as response:
                    if response.status == 200:
                        image_url = await response.text()
                        await interaction.followup.send(image_url)
                    else:
                        await interaction.followup.send(f"Failed to fetch image. API returned status: {response.status}")
            except aiohttp.ClientError as e:
                await interaction.followup.send(f"An error occurred while connecting to the API: {e}")
            except Exception as e:
                await interaction.followup.send(f"An unexpected error occurred: {e}")

async def setup(bot):
    await bot.add_cog(TetoImage(bot))