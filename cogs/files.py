import discord
from discord import app_commands
from discord.ext import commands

class Download(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    download = app_commands.Group(name="download", description="Download useful files")

    @download.command(name="open_otp", description="Get the OpenOTP installer link")
    async def open_otp(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Download OpenOTP Installer",
            description="[Click here to download OpenOTPInstaller.exe](https://filehost.internettools.org/OpenOTPInstaller.exe)",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    @download.command(name="archlinux", description="Get the Arch Linux ISO link")
    async def archlinux(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Download Arch Linux ISO",
            description="[Click here to download Arch Linux 2025.05.01 ISO](https://ftpmirror.infania.net/mirror/archlinux/iso/2025.05.01/)",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

    @download.command(name="ubuntu", description="Get the Ubuntu mirror link")
    async def ubuntu(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Download Ubuntu (Mirror)",
            description="[Click here for the Ubuntu mirror](https://launchpad.net/ubuntu/+mirror/ftp.yz.yamagata-u.ac.jp-release)",
            color=discord.Color.orange()
        )
        await interaction.response.send_message(embed=embed)

    @download.command(name="vscode_windows", description="Get the Visual Studio Code installer for Windows (ARM64)")
    async def vscode_windows(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Download Visual Studio Code for Windows (ARM64)",
            description="[Click here to download VS Code for Windows (ARM64)](https://code.visualstudio.com/sha/download?build=stable&os=win32-arm64-user)",
            color=discord.Color.purple()
        )
        await interaction.response.send_message(embed=embed)

    @download.command(name="vscode_mac", description="Get the Visual Studio Code installer for Mac (Universal)")
    async def vscode_mac(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Download Visual Studio Code for Mac (Universal)",
            description="[Click here to download VS Code for Mac (Universal)](https://code.visualstudio.com/sha/download?build=stable&os=darwin-universal)",
            color=discord.Color.dark_purple()
        )
        await interaction.response.send_message(embed=embed)

    async def cog_load(self):
        self.bot.tree.add_command(self.download)

async def setup(bot):
    await bot.add_cog(Download(bot))
