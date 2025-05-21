import discord
from discord.ext import commands
from discord import app_commands
import json
import os

class NotesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.filename = "notes.json"
        # Create the file if it doesn't exist
        if not os.path.exists(self.filename):
            with open(self.filename, "w") as f:
                json.dump({}, f, indent=4)

    def load_notes(self) -> dict:
        """Load and return the notes from the JSON file."""
        with open(self.filename, "r") as f:
            return json.load(f)

    def save_notes(self, data: dict) -> None:
        """Save the given notes dictionary to the JSON file."""
        with open(self.filename, "w") as f:
            json.dump(data, f, indent=4)

    @app_commands.command(name="takenotes", description="Take a note (supports markdown)")
    async def take_notes(self, interaction: discord.Interaction, note: str):
        """
        Adds a note for the user. The note can include markdown formatting.
        
        Usage: /takenotes note: Your markdown note here
        """
        # Load the current note data
        data = self.load_notes()
        user_id = str(interaction.user.id)

        # Make a list for the user if it doesn't yet exist
        if user_id not in data:
            data[user_id] = []

        # Append the new note and save the file back
        data[user_id].append(note)
        self.save_notes(data)

        await interaction.response.send_message("Your note has been saved.", ephemeral=True)

    @app_commands.command(name="notes", description="Display your saved notes")
    async def show_notes(self, interaction: discord.Interaction):
        """
        Displays all of your saved notes in an embed.
        
        Usage: /notes
        """
        data = self.load_notes()
        user_id = str(interaction.user.id)
        user_notes = data.get(user_id, [])

        embed = discord.Embed(
            title=f"{interaction.user.name}'s Notes",
            color=discord.Color.blue()
        )

        if user_notes:
            # Join notes with extra spacing; markdown will be rendered in the embed description
            formatted_notes = "\n\n".join(user_notes)
            embed.description = formatted_notes
        else:
            embed.description = "You have no notes saved. Use /takenotes to add one!"

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(NotesCog(bot))
