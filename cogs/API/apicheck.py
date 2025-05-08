import discord
from discord.ext import commands, tasks
import aiohttp
from discord import app_commands
import asyncio

class APICheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.urls = [
            "https://learnhelp.cc",
            "https://discordbot.learnhelp.cc",
            "https://api.learnhelp.cc/"
        ]

    async def check_url(self, session, url):
        try:
            async with session.get(url, timeout=5) as resp:
                return url, resp.status == 200
        except Exception:
            return url, False

    @app_commands.command(name="apicheck", description="Check the status of APIs.")
    async def apicheck(self, interaction: discord.Interaction):
        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(
                *(self.check_url(session, url) for url in self.urls)
            )

        embed = discord.Embed(title="API Status Check", color=discord.Color.blue())
        for url, status in results:
            status_str = "🟢 Online" if status else "🔴 Offline"
            embed.add_field(name=url, value=status_str, inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(APICheck(bot))
