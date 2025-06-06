import discord
from discord.ext import commands
from discord import app_commands
import json
import random

class RandomPhoneCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        # Load devices during cog initialization.
        self.devices = self.load_devices()

    def load_devices(self):
        try:
            with open("/home/server/wdiscordbotserver/data/devices.json", "r") as f:
                data = json.load(f)
                return data.get("RECORDS", [])
        except Exception as e:
            print(f"Error loading devices: {e}")
            return []

    @app_commands.command(
        name="randomphone",
        description="Selects a random smartphone from the dataset."
    )
    async def randomphone(self, interaction: discord.Interaction) -> None:
        if not self.devices:
            await interaction.response.send_message("No devices found!", ephemeral=True)
            return

        device = random.choice(self.devices)

        embed = discord.Embed(
            title=device.get("name", "Unknown Device"),
            description="Here is a randomly selected phone model:",
            color=discord.Color.blurple()
        )

        picture = device.get("picture", "")
        if picture:
            embed.set_thumbnail(url=picture)

        # Add key details as fields.
        embed.add_field(name="Released", value=device.get("released_at", "N/A"), inline=True)
        embed.add_field(name="Body", value=device.get("body", "N/A"), inline=True)
        embed.add_field(name="Operating System", value=device.get("os", "N/A"), inline=True)
        embed.add_field(name="Storage", value=device.get("storage", "N/A"), inline=True)
        embed.add_field(name="Display Resolution", value=device.get("display_resolution", "N/A"), inline=True)
        embed.add_field(name="Camera", value=device.get("camera_pixels", "N/A"), inline=True)

        # Process the specifications field.
        specs_string = device.get("specifications", "")
        try:
            specs_json = json.loads(specs_string)
            specs_formatted = "\n".join([f"**{key}:** {value}" for key, value in specs_json.items()])
        except Exception as e:
            specs_formatted = specs_string

        # Limit to Discord's field character limit.
        if len(specs_formatted) > 1024:
            specs_formatted = specs_formatted[:1021] + "..."
        embed.add_field(name="Specifications", value=specs_formatted or "N/A", inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RandomPhoneCog(bot))