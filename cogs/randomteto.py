import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

class RandomTeto(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="randomtetoimage", description="Get a random teto image")
    async def randomtetoimage(self, interaction: discord.Interaction):
        await interaction.response.defer()
        url = "https://slipstreamm.dev/teto"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    # Send the URL instead of the image file
                    await interaction.followup.send(url)
                else:
                    await interaction.followup.send("Failed to fetch image.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RandomTeto(bot))