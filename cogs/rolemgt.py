import discord
from discord.ext import commands
from discord import app_commands

class RoleManagerCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    role_group = app_commands.Group(name="role", description="Commands for managing server roles.")

    @role_group.command(
        name="create",
        description="Creates a new role with specified permissions and color."
    )
    @app_commands.describe(
        role_name="The name for the new role.",
        perms="Comma-separated permissions (e.g., send_messages,manage_channels).",
        color="Hex color value for the role (e.g., #FF5733)."
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role_create(self, interaction: discord.Interaction, role_name: str, perms: str, color: str):
        # Using interaction context now
        # Parse the permissions string into a discord.Permissions object.
        valid_perms = discord.Permissions.VALID_FLAGS
        kwargs = {}
        # Split by comma then go through each provided permission name.
        for perm_name_str in perms.split(','): # Renamed perm to perm_name_str
            perm_clean = perm_name_str.strip().lower()
            if perm_clean in valid_perms:
                kwargs[perm_clean] = True
            else:
                await interaction.response.send_message(f"Invalid permission name: `{perm_clean}`", ephemeral=True)
                return

        try:
            role_perms = discord.Permissions(**kwargs)
        except Exception as e:
            await interaction.response.send_message(f"Error setting permissions: {e}", ephemeral=True)
            return

        # Parse the hex color.
        try:
            # Remove a leading '#' if present and convert.
            color_int = int(color.lstrip('#'), 16)
            role_color = discord.Color(color_int)
        except ValueError:
            await interaction.response.send_message("Invalid color format. Please provide a valid hex value (e.g. #FF5733).", ephemeral=True)
            return

        try:
            new_role = await interaction.guild.create_role( # Renamed role to new_role
                name=role_name,
                permissions=role_perms,
                colour=role_color,
                reason=f"Role created by {interaction.user}"
            )
            await interaction.response.send_message(f"Role `{new_role.name}` created successfully.")
        except Exception as e:
            await interaction.response.send_message(f"Failed to create role: {e}", ephemeral=True)

    @role_group.command(
        name="viewperms",
        description="Displays the enabled permissions of a role."
    )
    @app_commands.describe(role="The role to view permissions for.")
    async def role_viewperms(self, interaction: discord.Interaction, role: discord.Role):
        # Convert the permissions to a dictionary and build a list of enabled permissions.
        perms_dict = role.permissions.to_dict()
        enabled_perms = [perm.replace("_", " ").title() for perm, value in perms_dict.items() if value]
        description = "\n".join(enabled_perms) if enabled_perms else "No permissions enabled."
        embed = discord.Embed(
            title=f"Permissions for Role: {role.name}",
            description=description,
            color=role.colour
        )
        await interaction.response.send_message(embed=embed)

    @role_group.command(
        name="add",
        description="Adds a role to a member."
    )
    @app_commands.describe(member="The member to add the role to.", role="The role to add.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role_add(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        try:
            await member.add_roles(role, reason=f"Role added by {interaction.user}")
            await interaction.response.send_message(f"Role `{role.name}` added to {member.mention}.")
        except Exception as e:
            await interaction.response.send_message(f"Failed to add role: {e}", ephemeral=True)

    @role_group.command(
        name="remove",
        description="Removes a role from a member."
    )
    @app_commands.describe(member="The member to remove the role from.", role="The role to remove.")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role_remove(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        try:
            await member.remove_roles(role, reason=f"Role removed by {interaction.user}")
            await interaction.response.send_message(f"Role `{role.name}` removed from {member.mention}.")
        except Exception as e:
            await interaction.response.send_message(f"Failed to remove role: {e}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RoleManagerCog(bot))
