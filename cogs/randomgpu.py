import discord
from discord import app_commands
from discord.ext import commands
import json
import random

class GPU(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.gpu_file = "/home/server/wdiscordbotserver/data/allgpus.json"
        self.gpus = self.load_gpus()

    def load_gpus(self):
        """Load GPU data from the provided JSON file."""
        try:
            with open(self.gpu_file, 'r') as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error loading GPU data: {e}")
            return []

    @app_commands.command(name="randomgpu", description="Displays info about a random GPU")
    async def gpu_command(self, interaction: discord.Interaction) -> None:
        if not self.gpus:
            await interaction.response.send_message("No GPU data available!")
            return

        # Select a random GPU
        selected_gpu = random.choice(self.gpus)

        # Build a description with all the key/value pairs.
        description_lines = [f"**{key}:** {value}" for key, value in selected_gpu.items()]
        description = "\n".join(description_lines)

        embed = discord.Embed(
            title=selected_gpu.get("Name", "GPU Information"),
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text="GPU data loaded from allgpus.json")

        # Respond to the interaction with the embed
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(GPU(bot))