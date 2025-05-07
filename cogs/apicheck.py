import discord
from discord.ext import commands, tasks
import aiohttp

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

    @commands.command(name="apicheck")
    async def apicheck(self, ctx):
        async with aiohttp.ClientSession() as session:
            results = await asyncio.gather(
                *(self.check_url(session, url) for url in self.urls)
            )

        embed = discord.Embed(title="API Status Check", color=discord.Color.blue())
        for url, status in results:
            status_str = "🟢 Online" if status else "🔴 Offline"
            embed.add_field(name=url, value=status_str, inline=False)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(APICheck(bot))