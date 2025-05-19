import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import random

class TetoImage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://safebooru.org/index.php"

    @app_commands.command(name="randomtetoimage", description="Gets a random Kasane Teto image from Safebooru")
    async def random_teto_image(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Acknowledge the interaction immediately

        params = {
            "page": "dapi",
            "s": "post",
            "q": "index",
            "tags": "kasane_teto",
            "limit": 100,  # Request up to 100 images
            "json": 1
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            # Safebooru returns a list of posts, pick a random one
                            random_post = random.choice(data)
                            image_url = random_post.get('file_url')
                            if image_url:
                                await interaction.followup.send(image_url)
                            else:
                                await interaction.followup.send("Could not find a valid image URL in the response.")
                        else:
                            await interaction.followup.send("No images found for 'kasane_teto'.")
                    else:
                        await interaction.followup.send(f"Failed to fetch images from Safebooru. API returned status: {response.status}")
            except aiohttp.ClientError as e:
                await interaction.followup.send(f"An error occurred while connecting to Safebooru API: {e}")
            except Exception as e:
                await interaction.followup.send(f"An unexpected error occurred: {e}")

async def setup(bot):
    await bot.add_cog(TetoImage(bot))