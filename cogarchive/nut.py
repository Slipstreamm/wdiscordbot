import discord
from discord import app_commands
from discord.ext import commands

class ExampleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    actions_group = app_commands.Group(name="actions", description="User action and roleplay commands.")

    @actions_group.command(name="sa", description="sa a user.")
    async def sa_command(self, interaction: discord.Interaction, member: discord.Member): # Renamed method
        await interaction.response.send_message(f"{interaction.user.mention} groped {member.mention} on a japanese train")

    @actions_group.command(name="bootyfuck", description="bootyfuck to a user.")
    async def bootyfuck_command(self, interaction: discord.Interaction, member: discord.Member): # Renamed method
        await interaction.response.send_message(f"{interaction.user.mention} fucked {member.mention} in they ass")

    @actions_group.command(name="rape", description="rape a user.")       
    async def rape_command(self, interaction: discord.Interaction, member: discord.Member): # Renamed method
        await interaction.response.send_message(f"{interaction.user.mention} raped {member.mention}") # Used interaction.user.mention for consistency

async def setup(bot):
    await bot.add_cog(ExampleCog(bot))
