import os
import discord
from discord.ext import commands
from discord import app_commands
import re
import asyncio
import sys

class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ping_group = app_commands.Group(name="ping", description="Commands to check latency and ping hosts.")

    @ping_group.command(name="bot", description="Responds with the bot's WebSocket latency.")
    async def ping_bot(self, interaction: discord.Interaction):
        """Responds with the bot's latency."""
        latency = self.bot.latency * 1000  # Convert to milliseconds
        await interaction.response.send_message(f"Pong! Latency: {latency:.2f}ms")

    @ping_group.command(name="host", description="Ping a remote IP/domain using ICMP.")
    @app_commands.describe(host="The IP address or domain name to ping.")
    async def ping_host(self, interaction: discord.Interaction, host: str):
        """Ping a remote ip/domain using ICMP."""

        # Strict regex for IPv4, IPv6, and domain names
        ip_regex = r"^(?:(?:[0-9]{1,3}\.){3}[0-9]{1,3}|(?:[a-fA-F0-9:]+))$"
        domain_regex = r"^(?=.{1,253}$)(?!\-)([a-zA-Z0-9\-]{1,63}\.)+[a-zA-Z]{2,63}$"
        if not (re.match(ip_regex, host) or re.match(domain_regex, host)):
            await interaction.response.send_message("Invalid host. Please provide a valid IP address or domain name.", ephemeral=True)
            return

        await interaction.response.send_message(f"Pinging {host}...")

        try:
            param = "-n" if os.name == "nt" else "-c"
            # Use asyncio to avoid blocking
            proc = await asyncio.create_subprocess_exec(
                "ping", param, "1", host,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            output = stdout.decode(errors="ignore") + stderr.decode(errors="ignore")

            # Ignore any unreachable code warnings here.
            # Pylance static analysis thinks that os.name will always evaluate to the value that is true for your system.
            # But in reality, it can be either depending on the environment.
            latency_msg = ""
            if os.name == "nt":
                # Windows: Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms
                match = re.search(r"Minimum = (\d+)ms, Maximum = (\d+)ms, Average = (\d+)ms", output)
                if match:
                    latency_msg = f"Min: {match.group(1)}ms, Max: {match.group(2)}ms, Avg: {match.group(3)}ms"
            else:
                # Unix: rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms
                match = re.search(r"rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+) ms", output)
                if match:
                    latency_msg = f"Min: {match.group(1)}ms, Avg: {match.group(2)}ms, Max: {match.group(3)}ms, Mdev: {match.group(4)}ms"

            if proc.returncode == 0:
                msg = f"{host} is up!"
                if latency_msg:
                    msg += f" {latency_msg}"
                await interaction.edit_original_response(content=msg)
            else:
                await interaction.edit_original_response(content=f"{host} is down!")
        except Exception as e:
            await interaction.edit_original_response(content=f"Error: {e}")


async def setup(bot):
    await bot.add_cog(Ping(bot))
