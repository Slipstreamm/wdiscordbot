import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import re

PASTEBIN_API_URL = "http://pastebin.internettools.org/api/paste"

MESSAGE_LINK_RE = re.compile(
    r"https://(?:canary\.|ptb\.)?discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)"
)

class PastebinMessageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="share",
        description="Share a Discord message as a Pastebin link."
    )
    @app_commands.describe(message_link="The link to the Discord message to share")
    async def share(self, interaction: discord.Interaction, message_link: str):
        await interaction.response.defer(thinking=True)
        match = MESSAGE_LINK_RE.match(message_link)
        if not match:
            await interaction.followup.send("Invalid message link format.", ephemeral=True)
            return

        guild_id, channel_id, message_id = map(int, match.groups())
        channel = self.bot.get_channel(channel_id)
        if channel is None:
            # Try fetching the channel if not cached
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception:
                await interaction.followup.send("Could not find the channel.", ephemeral=True)
                return

        try:
            message = await channel.fetch_message(message_id)
        except Exception:
            await interaction.followup.send("Could not fetch the message.", ephemeral=True)
            return

        content = message.content
        if not content:
            await interaction.followup.send("The message has no text content to share.", ephemeral=True)
            return

        # Create paste
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    PASTEBIN_API_URL,
                    json={"content": content},
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    if resp.status == 201:
                        data = await resp.json()
                        paste_url = data.get("url")
                        await interaction.followup.send(
                            f"Pastebin link: {paste_url}"
                        )
                    else:
                        error = await resp.json()
                        await interaction.followup.send(
                            f"Failed to create paste: {error.get('error', 'Unknown error')}",
                            ephemeral=True
                        )
            except Exception as e:
                await interaction.followup.send(
                    f"Error communicating with Pastebin API: {e}",
                    ephemeral=True
                )

async def setup(bot):
    await bot.add_cog(PastebinMessageCog(bot))
