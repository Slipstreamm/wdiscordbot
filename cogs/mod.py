import discord
from discord import app_commands
from discord.ext import commands

class Moderation(commands.Cog):
    """Moderation commands for server management."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def send_log(self, interaction: discord.Interaction, action: str, target: discord.Member, reason: str = None):
        """Send moderation actions to a logging channel."""
        log_channel = discord.utils.get(interaction.guild.channels, name="mod-logs")  # Change channel name as needed
        if log_channel:
            embed = discord.Embed(
                title=f"Moderation Action: {action}",
                description=f"**User:** {target.mention}\n**Moderator:** {interaction.user.mention}\n**Reason:** {reason or 'No reason provided'}",
                color=discord.Color.red(),
            )
            await log_channel.send(embed=embed)

    @app_commands.command(name="kick", description="Kick a user from the server.")
    @app_commands.describe(member="The user to kick", reason="Reason for kicking the user")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if interaction.user.guild_permissions.kick_members:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"🚨 **{member}** has been kicked.\nReason: {reason or 'No reason provided'}")
            await self.send_log(interaction, "Kick", member, reason)
        else:
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

    @app_commands.command(name="ban", description="Ban a user from the server.")
    @app_commands.describe(member="The user to ban", reason="Reason for banning the user")
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if interaction.user.guild_permissions.ban_members:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"🚨 **{member}** has been banned.\nReason: {reason or 'No reason provided'}")
            await self.send_log(interaction, "Ban", member, reason)
        else:
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

    @app_commands.command(name="timeout", description="Timeout (mute) a user for a specified duration.")
    @app_commands.describe(member="The user to mute", duration="Mute duration in seconds", reason="Reason for muting")
    async def timeout(self, interaction: discord.Interaction, member: discord.Member, duration: int, reason: str = None):
        if interaction.user.guild_permissions.moderate_members:
            await member.timeout_for(duration=discord.utils.utcnow() + discord.utils.timedelta(seconds=duration), reason=reason)
            await interaction.response.send_message(f"⏳ **{member}** has been muted for **{duration} seconds**.\nReason: {reason or 'No reason provided'}")
            await self.send_log(interaction, "Timeout", member, reason)
        else:
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

    @app_commands.command(name="purge", description="Delete a number of messages in a channel.")
    @app_commands.describe(amount="Number of messages to delete (max 100)")
    async def purge(self, interaction: discord.Interaction, amount: int):
        if interaction.user.guild_permissions.manage_messages:
            if amount <= 100:
                await interaction.channel.purge(limit=amount)
                await interaction.response.send_message(f"🗑 **{amount} messages** have been deleted!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ You can only delete up to **100** messages at a time.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

    @app_commands.command(name="warn", description="Warn a user (no actual punishment).")
    @app_commands.describe(member="The user to warn", reason="Reason for warning")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, reason: str):
        if interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message(f"⚠️ **{member}** has been warned.\nReason: {reason}")
            await self.send_log(interaction, "Warning", member, reason)
        else:
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

    @app_commands.command(name="unban", description="Unban a user by their ID.")
    @app_commands.describe(user_id="The ID of the user to unban")
    async def unban(self, interaction: discord.Interaction, user_id: int):
        if interaction.user.guild_permissions.ban_members:
            user = discord.Object(id=user_id)
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"🔓 **User with ID `{user_id}` has been unbanned.**")
        else:
            await interaction.response.send_message("❌ You don't have permission to use this command.", ephemeral=True)

# Cog Setup
async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))
