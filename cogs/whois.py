import discord
from discord import app_commands
from discord.ext import commands
import whois

class Whois(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="whois", description="Lookup WHOIS info for a domain")
    @app_commands.describe(domain="The domain to lookup (e.g. example.com)")
    async def whois(self, interaction: discord.Interaction, domain: str):
        await interaction.response.defer()
        try:
            w = await self.bot.loop.run_in_executor(None, whois.whois, domain)
        except Exception as e:
            await interaction.followup.send(f"Failed to fetch WHOIS info: {e}")
            return
        if not w or not w.get("domain_name"):
            await interaction.followup.send("Could not find WHOIS info for that domain.")
            return
        # Prepare a summary of WHOIS info
        info = []
        for key in ["domain_name", "registrar", "creation_date", "expiration_date", "name_servers", "status"]:
            value = w.get(key)
            if value:
                info.append(f"**{key.replace('_', ' ').title()}:** {value}")
        text = "\n".join(info)
        if not text:
            text = "No WHOIS info available."
        embed = discord.Embed(
            title=f"WHOIS info for {domain}",
            description=text,
            color=discord.Color.blue()
        )
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Whois(bot))
