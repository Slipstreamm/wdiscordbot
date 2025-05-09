import discord
from discord.ext import commands
from discord import app_commands
import os
import json

# Path to the JSON config file
CONFIG_FILE = "/home/server/serverconfig.json"

def load_config() -> dict:
    """Load the server configuration from file.
    If the file does not exist or is invalid, create a new empty configuration."""
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_config(data: dict) -> None:
    """Save the configuration JSON to file."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

async def global_disabled_check(interaction: discord.Interaction) -> bool:
    """
    Global check for all app (slash) commands.
    If the command (except for serverconfig itself) is marked as disabled in this server’s config,
    send an ephemeral message and prevent execution.
    """
    # If interaction comes from a DM, allow it.
    if interaction.guild is None:
        return True

    # Always allow the serverconfig command so admins can change settings.
    if interaction.command and interaction.command.name == "serverconfig":
        return True

    config = load_config()
    guild_id = str(interaction.guild.id)
    disabled_commands = config.get(guild_id, [])

    if interaction.command and interaction.command.name in disabled_commands:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "This command has been disabled by server admins.", ephemeral=True
            )
        # Raising a CheckFailure prevents the command from running.
        raise app_commands.CheckFailure("Command disabled.")
    return True

class ServerConfigCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="serverconfig", 
        description="Enable or disable a command in this server."
    )
    @app_commands.describe(
        command="The name of the command to configure",
        enabled="Type 'yes' to enable or 'no' to disable."
    )
    async def serverconfig(
        self, 
        interaction: discord.Interaction, 
        command: str, 
        enabled: str
    ):
        # Check if the user has admin permissions.
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "You do not have permission to use this command.", 
                ephemeral=True
            )
            return

        # Normalize the enabled flag.
        enabled_flag = enabled.lower()
        if enabled_flag not in ["yes", "no"]:
            await interaction.response.send_message(
                "Invalid 'enabled' option. Please use 'yes' or 'no'.", 
                ephemeral=True
            )
            return

        # Verify that the provided command exists.
        found = False
        # Check the classic text commands.
        for cmd in self.bot.commands:
            if cmd.name == command:
                found = True
                break
        # Also check application (slash) commands from the tree.
        if not found:
            for cmd in self.bot.tree.get_commands():
                if cmd.name == command:
                    found = True
                    break
        if not found:
            await interaction.response.send_message(
                f"The command '{command}' was not found.", 
                ephemeral=True
            )
            return

        # Load the configuration.
        config = load_config()
        guild_id = str(interaction.guild.id)
        if guild_id not in config:
            config[guild_id] = []

        if enabled_flag == "no":
            # Add the command to the disabled list if not already present.
            if command not in config[guild_id]:
                config[guild_id].append(command)
                save_config(config)
            await interaction.response.send_message(
                f"Command '{command}' has been **disabled** in this server.", 
                ephemeral=True
            )
        else:  # enabled_flag == "yes"
            # Remove the command from the disabled list if present.
            if command in config[guild_id]:
                config[guild_id].remove(command)
                save_config(config)
            await interaction.response.send_message(
                f"Command '{command}' has been **enabled** in this server.", 
                ephemeral=True
            )

    @serverconfig.autocomplete("command")
    async def command_autocomplete(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        """
        Autocomplete for the 'command' parameter.
        It searches both classic and slash commands for matches.
        """
        choices = set()
        # Get names of text commands.
        for cmd in self.bot.commands:
            choices.add(cmd.name)
        # Get names of app commands.
        for cmd in self.bot.tree.get_commands():
            choices.add(cmd.name)
        # Filter and send at most 25 matching choices.
        filtered = [
            app_commands.Choice(name=cmd, value=cmd)
            for cmd in choices
            if current.lower() in cmd.lower()
        ]
        return filtered[:25]

async def setup(bot: commands.Bot):
    # Register the global check – it will run for every application (slash) command.
    bot.tree.add_check(global_disabled_check)
    await bot.add_cog(ServerConfigCog(bot))
