import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import io

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
                    img_bytes = await resp.read()
                    file = discord.File(io.BytesIO(img_bytes), filename="teto.jpg")
                    await interaction.followup.send(file=file)
                else:
                    await interaction.followup.send("Failed to fetch image.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RandomTeto(bot))