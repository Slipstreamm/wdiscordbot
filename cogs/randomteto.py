import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import random

class TetoImageView(discord.ui.View):
    def __init__(self, image_urls, current_index, history, message_id, bot):
        super().__init__(timeout=180)
        self.image_urls = image_urls
        self.current_index = current_index
        self.history = history
        self.message_id = message_id
        self.bot = bot

    async def update_message(self, interaction):
        embed = discord.Embed(
            title="Random Kasane Teto Image",
            color=discord.Color.pink()
        )
        embed.set_image(url=self.image_urls[self.current_index])
        embed.set_footer(text=f"Image {self.current_index + 1} of {len(self.image_urls)}")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, custom_id="teto_prev")
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_index > 0:
            self.current_index -= 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, custom_id="teto_next")
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.current_index < len(self.image_urls) - 1:
            self.current_index += 1
            await self.update_message(interaction)
        else:
            await interaction.response.defer()

    @discord.ui.button(label="New Random", style=discord.ButtonStyle.primary, custom_id="teto_new")
    async def new_random(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Fetch new images and reset history
        cog = self.bot.get_cog("TetoImage")
        if cog:
            new_urls = await cog.fetch_teto_images()
            if new_urls:
                self.image_urls = new_urls
                self.current_index = 0
                self.history[self.message_id] = (self.image_urls, self.current_index)
                await self.update_message(interaction)
            else:
                await interaction.response.send_message("Failed to fetch new images.", ephemeral=True)
        else:
            await interaction.response.send_message("Cog not found.", ephemeral=True)

class TetoImage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.base_url = "https://safebooru.org/index.php"
        self.history = {}  # message_id: (image_urls, current_index)

    async def fetch_teto_images(self):
        params = {
            "page": "dapi",
            "s": "post",
            "q": "index",
            "tags": "kasane_teto",
            "limit": 100,
            "json": 1
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data:
                            urls = [post.get('file_url') for post in data if post.get('file_url')]
                            return urls
            except Exception:
                pass
        return []

    @app_commands.command(name="randomtetoimage", description="Gets a random Kasane Teto image from Safebooru")
    async def random_teto_image(self, interaction: discord.Interaction):
        await interaction.response.defer()
        image_urls = await self.fetch_teto_images()
        if not image_urls:
            await interaction.followup.send("No images found for 'kasane_teto'.")
            return
        current_index = random.randint(0, len(image_urls) - 1)
        embed = discord.Embed(
            title="Random Kasane Teto Image",
            color=discord.Color.pink()
        )
        embed.set_image(url=image_urls[current_index])
        embed.set_footer(text=f"Image {current_index + 1} of {len(image_urls)}")
        view = TetoImageView(image_urls, current_index, self.history, None, self.bot)
        msg = await interaction.followup.send(embed=embed, view=view)
        view.message_id = msg.id
        self.history[msg.id] = (image_urls, current_index)

async def setup(bot):
    await bot.add_cog(TetoImage(bot))