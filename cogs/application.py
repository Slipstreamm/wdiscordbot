import discord
from discord.ext import commands
from discord import app_commands

class ApplicationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # This will store the Google Forms link for applications.
        self.apply_link = None

    application_group = app_commands.Group(name="application", description="Commands for managing and getting the application link.")

    # --------------------------------------------------------------------------
    # Set Application Link Command
    # --------------------------------------------------------------------------
    @application_group.command(name="set", description="Set the Google Forms link for applications. (Admin Only)")
    @app_commands.describe(link="The Google Forms link for applications.")
    @app_commands.checks.has_permissions(administrator=True)
    async def application_set(self, interaction: discord.Interaction, link: str):
        # Optionally, add basic validation for the link here.
        self.apply_link = link
        await interaction.response.send_message(f"Application link has been set to:\n{link}")

    # --------------------------------------------------------------------------
    # Clear Application Link Command
    # --------------------------------------------------------------------------
    @application_group.command(name="clear", description="Clear the currently set Google Forms link for applications. (Admin Only)")
    @app_commands.checks.has_permissions(administrator=True)
    async def application_clear(self, interaction: discord.Interaction):
        self.apply_link = None
        await interaction.response.send_message("Application link has been cleared.")

    # --------------------------------------------------------------------------
    # Apply Command
    # --------------------------------------------------------------------------
    @application_group.command(name="get", description="Receive the application link via DM.")
    async def application_get(self, interaction: discord.Interaction):
        if self.apply_link is None:
            await interaction.response.send_message("No application link has been set yet. Please contact an administrator.", ephemeral=True)
            return

        try:
            # Attempt to create or fetch the user's DM channel
            dm_channel = await interaction.user.create_dm()
            await dm_channel.send(f"Here is your application link:\n{self.apply_link}")
            await interaction.response.send_message("I've sent the application link to your DMs.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Unable to DM you the application link: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ApplicationCog(bot))
