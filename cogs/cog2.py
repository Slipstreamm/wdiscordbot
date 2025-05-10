import discord
from discord.ext import commands
from discord import app_commands

# Define the owner check predicate
async def owner_check_predicate(interaction: discord.Interaction) -> bool:
    return await interaction.client.is_owner(interaction.user)

class CogManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def format_loaded_cogs(self):
        """Return a sorted string of all loaded cog extensions."""
        if self.bot.extensions:
            return "\n".join(sorted(self.bot.extensions.keys()))
        return "No extensions loaded."

    cogctl_group = app_commands.Group(name="cogctl", description="Commands for managing bot cogs. (Owner Only)")

    @cogctl_group.command(name="list", description="Displays all loaded cogs/extensions.")
    @app_commands.check(owner_check_predicate)
    async def cogctl_list(self, interaction: discord.Interaction):
        loaded = self.format_loaded_cogs()
        message = f"Loaded Cogs:\n{loaded}"
        await interaction.response.send_message(f"```\n{message}\n```", ephemeral=True)

    @cogctl_group.command(
        name="unload",
        description="Disables/unloads a cog and reloads all other cogs."
    )
    @app_commands.describe(cog="Name of the cog to unload (e.g., fun, ai, cogs.ai).")
    @app_commands.check(owner_check_predicate)
    async def cogctl_unload(self, interaction: discord.Interaction, cog: str):
        await interaction.response.defer(ephemeral=True)
        output_lines = []
        # If needed, prepend "cogs." to the cog name
        extension = cog if cog.startswith("cogs.") else f"cogs.{cog}"
        output_lines.append(f"Attempting to unload cog: {extension}")

        # Check if the extension is loaded.
        if extension not in self.bot.extensions:
            await interaction.followup.send(f"Cog `{extension}` is not currently loaded.")
            return

        try:
            await self.bot.unload_extension(extension)
            output_lines.append(f"Successfully unloaded `{extension}`.")
        except Exception as e:
            output_lines.append(f"Failed to unload `{extension}`: {e}")
            await interaction.followup.send(f"```\n" + "\n".join(output_lines) + "\n```")
            return

        # Reload all remaining loaded cogs
        output_lines.append("Reloading remaining cogs:")
        for ext_name in list(self.bot.extensions.keys()): # Use a different var name to avoid conflict
            try:
                await self.bot.reload_extension(ext_name)
                output_lines.append(f"Reloaded: {ext_name}")
            except Exception as e:
                output_lines.append(f"Failed to reload {ext_name}: {e}")

        output_lines.append("Currently loaded cogs:")
        output_lines.append(self.format_loaded_cogs())

        await interaction.followup.send(f"```\n" + "\n".join(output_lines) + "\n```")

    @cogctl_group.command(
        name="load",
        description="Enables/loads a disabled cog and reloads all cogs."
    )
    @app_commands.describe(cog="Name of the cog to load (e.g., fun, ai, cogs.ai).")
    @app_commands.check(owner_check_predicate)
    async def cogctl_load(self, interaction: discord.Interaction, cog: str):
        await interaction.response.defer(ephemeral=True)
        output_lines = []
        extension = cog if cog.startswith("cogs.") else f"cogs.{cog}"
        output_lines.append(f"Attempting to load cog: {extension}")

        if extension in self.bot.extensions:
            await interaction.followup.send(f"Cog `{extension}` is already loaded.")
            return

        try:
            await self.bot.load_extension(extension)
            output_lines.append(f"Successfully loaded `{extension}`.")
        except Exception as e:
            output_lines.append(f"Failed to load `{extension}`: {e}")
            await interaction.followup.send(f"```\n" + "\n".join(output_lines) + "\n```")
            return

        # Reload all currently loaded cogs
        output_lines.append("Reloading all cogs:")
        for ext_name in list(self.bot.extensions.keys()): # Use a different var name
            try:
                await self.bot.reload_extension(ext_name)
                output_lines.append(f"Reloaded: {ext_name}")
            except Exception as e:
                output_lines.append(f"Failed to reload {ext_name}: {e}")

        output_lines.append("Currently loaded cogs:")
        output_lines.append(self.format_loaded_cogs())

        await interaction.followup.send(f"```\n" + "\n".join(output_lines) + "\n```")

async def setup(bot):
    await bot.add_cog(CogManagerCog(bot))
