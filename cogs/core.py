# cogs/core.py
import os
import platform
import psutil
import discord
from discord.ext import commands
from discord import app_commands
import shutil
import subprocess
import asyncio
import logging
import time
import GPUtil
import distro

# Import wmi for Windows motherboard info
try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False

class Core(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="sysinfo", description="Shows the hardware information of the server.")
    async def sysinfo(self, interaction: discord.Interaction):
        # (The CPU, RAM, and other details are hard-coded here as an example.)
        embed = discord.Embed(title="Kasanes pc >.<", color=discord.Color.blue())
        embed.add_field(name="System", value="PowerEdge R7715 ラックサーバー", inline=False)
        embed.add_field(name="OS", value="ubuntu 24.10", inline=False)
        embed.add_field(name="Processor", value="AMD EPYC 9175F 4.20GHz", inline=False)
        embed.add_field(name="RAM", value="768 GB", inline=False)
        embed.add_field(name="Disk Space", value="480 GB", inline=False)
        embed.add_field(name="Server Name", value="Freaky teto :3", inline=False)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="systemcheck", description="Shows detailed system and bot information.")
    async def systemcheck(self, interaction: discord.Interaction):
        """Check the bot and system status."""
        # Defer the response to prevent interaction timeout
        await interaction.response.defer(thinking=True)
        try:
            embed = await self._system_check_logic(interaction)
            await interaction.followup.send(embed=embed)
        except Exception as e:
            print(f"Error in systemcheck command: {e}")
            await interaction.followup.send(f"An error occurred while checking system status: {e}")

    async def _system_check_logic(self, context_or_interaction):
        """Return detailed bot and system information as a Discord embed."""
        # Bot information
        bot_user = self.bot.user
        guild_count = len(self.bot.guilds)

        # More efficient member counting - use cached members when available
        # This avoids API calls that can cause timeouts
        user_ids = set()
        for guild in self.bot.guilds:
            try:
                # Use members that are already cached
                for member in guild.members:
                    if not member.bot:
                        user_ids.add(member.id)
            except Exception as e:
                print(f"Error counting members in guild {guild.name}: {e}")
        user_count = len(user_ids)

        # System information
        system = platform.system()
        os_info = f"{system} {platform.release()}"
        hostname = platform.node()
        distro_info_str = ""  # Renamed variable

        if system == "Linux":
            try:
                # Use distro library for better Linux distribution detection
                distro_name = distro.name(pretty=True)
                distro_info_str = f"\n**Distro:** {distro_name}"
            except ImportError:
                distro_info_str = "\n**Distro:** (Install 'distro' package for details)"
            except Exception as e:
                distro_info_str = f"\n**Distro:** (Error getting info: {e})"
        elif system == "Windows":
            # Add Windows version details if possible
            try:
                win_ver = platform.version()  # e.g., '10.0.19041'
                win_build = platform.win32_ver()[1]  # e.g., '19041'
                os_info = f"Windows {win_ver} (Build {win_build})"
            except Exception as e:
                print(f"Could not get detailed Windows version: {e}")
                # Keep the basic os_info

        uptime_seconds = time.time() - psutil.boot_time()
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)

        uptime_str = ""
        if days > 0:
            uptime_str += f"{int(days)}d "
        uptime_str += f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
        uptime = uptime_str.strip()

        # Hardware information - use a shorter interval for CPU usage
        cpu_usage = psutil.cpu_percent(interval=0.1)

        # Get CPU info with a timeout to prevent hanging
        try:
            # Use a simpler approach for CPU name to avoid potential slowdowns
            if platform.system() == "Windows":
                cpu_name_base = platform.processor()
            elif platform.system() == "Linux":
                try:
                    with open("/proc/cpuinfo", "r") as f:
                        for line in f:
                            if line.startswith("model name"):
                                cpu_name_base = line.split(":")[1].strip()
                                break
                        else:
                            cpu_name_base = "Unknown CPU"
                except:
                    cpu_name_base = platform.processor() or "Unknown CPU"
            else:
                cpu_name_base = platform.processor() or "Unknown CPU"

            physical_cores = psutil.cpu_count(logical=False)
            total_threads = psutil.cpu_count(logical=True)
            cpu_name = f"{cpu_name_base} ({physical_cores}C/{total_threads}T)"
        except Exception as e:
            print(f"Error getting CPU info: {e}")
            cpu_name = "N/A"

        # Get motherboard information
        motherboard_info = self._get_motherboard_info()

        memory = psutil.virtual_memory()
        ram_usage = f"{memory.used // (1024 ** 2)} MB / {memory.total // (1024 ** 2)} MB ({memory.percent}%)"

        # GPU Information (using GPUtil for cross-platform consistency if available)
        gpu_info_lines = []
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                for gpu in gpus:
                    gpu_info_lines.append(
                        f"{gpu.name} ({gpu.load*100:.1f}% Load, {gpu.memoryUsed:.0f}/{gpu.memoryTotal:.0f} MB VRAM)"
                    )
                gpu_info = "\n".join(gpu_info_lines)
            else:
                gpu_info = "No dedicated GPU detected by GPUtil."
        except ImportError:
            gpu_info = "GPUtil library not installed. Cannot get detailed GPU info."
        except Exception as e:
            print(f"Error getting GPU info via GPUtil: {e}")
            gpu_info = f"Error retrieving GPU info: {e}"

        # Determine user and avatar URL based on context type
        if isinstance(context_or_interaction, commands.Context):
            user = context_or_interaction.author
            avatar_url = user.display_avatar.url
        elif isinstance(context_or_interaction, discord.Interaction):
            user = context_or_interaction.user
            avatar_url = user.display_avatar.url
        else:
            # Fallback or handle error if needed
            user = self.bot.user  # Or some default
            avatar_url = self.bot.user.display_avatar.url if self.bot.user else None

        # Create embed
        embed = discord.Embed(title="📊 System Status", color=discord.Color.blue())
        if bot_user:
            embed.set_thumbnail(url=bot_user.display_avatar.url)

        # Bot Info Field
        if bot_user:
            embed.add_field(
                name="🤖 Bot Information",
                value=f"**Name:** {bot_user.name}\n"
                      f"**ID:** {bot_user.id}\n"
                      f"**Servers:** {guild_count}\n"
                      f"**Unique Users:** {user_count}",
                inline=False
            )
        else:
            embed.add_field(
                name="🤖 Bot Information",
                value="Bot user information not available.",
                inline=False
            )

        # System Info Field
        embed.add_field(
            name="🖥️ System Information",
            value=f"**OS:** {os_info}{distro_info_str}\n"  # Use renamed variable
                  f"**Hostname:** {hostname}\n"
                  f"**Uptime:** {uptime}",
            inline=False
        )

        # Hardware Info Field
        embed.add_field(
            name="⚙️ Hardware Information",
            value=f"**Device Model:** {motherboard_info}\n"
                  f"**CPU:** {cpu_name}\n"
                  f"**CPU Usage:** {cpu_usage}%\n"
                  f"**RAM Usage:** {ram_usage}\n"
                  f"**GPU Info:**\n{gpu_info}",
            inline=False
        )

        if user:
            embed.set_footer(text=f"Requested by: {user.display_name}", icon_url=avatar_url)

        embed.timestamp = discord.utils.utcnow()
        return embed

    def _get_motherboard_info(self):
        """Get motherboard information based on the operating system."""
        system = platform.system()
        try:
            if system == "Windows":
                if WMI_AVAILABLE:
                    w = wmi.WMI()
                    for board in w.Win32_BaseBoard():
                        return f"{board.Manufacturer} {board.Product}"
                return "WMI module not available"
            elif system == "Linux":
                # Read motherboard product name from sysfs
                try:
                    with open("/sys/devices/virtual/dmi/id/product_name", "r") as f:
                        product_name = f.read().strip()
                    return product_name if product_name else "Unknown motherboard"
                except FileNotFoundError:
                    return "/sys/devices/virtual/dmi/id/product_name not found"
                except Exception as e:
                    return f"Error reading motherboard info: {e}"
            else:
                return f"Unsupported OS: {system}"
        except Exception as e:
            print(f"Error getting motherboard info: {e}")
            return "Error retrieving motherboard info"

    @app_commands.command(name="status", description="Sets the bot's status to the provided text.")
    async def status(self, interaction: discord.Interaction, text: str):
        await self.bot.change_presence(activity=discord.Game(name=text))
        await interaction.response.send_message(f"Bot status updated to: **{text}**")

    @app_commands.command(name="user", description="Changes the bot's nickname to the provided text.")
    async def user(self, interaction: discord.Interaction, text: str):
        if interaction.guild is None:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return
        try:
            await interaction.guild.me.edit(nick=text)
            await interaction.response.send_message(f"Bot nickname changed to: **{text}**")
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to change my nickname.", ephemeral=True)

    @app_commands.command(name="say", description="Make the bot say something.")
    async def say(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(f"Message sent: {message}", ephemeral=True)
        await interaction.channel.send(message)

    @app_commands.command(name="help", description="Lists all available commands")
    async def help_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Help Command",
            description="Here is a list of all the available commands:",
            color=discord.Color.blurple()
        )
        commands_list = [
            ("/sysinfo", "Shows the hardware information of the server."),
            ("/systemcheck", "Shows detailed system and bot information."),
            ("/status", "Sets the bot's status to the provided text."),
            ("/user", "Changes the bot's nickname."),
            ("/ping", "Pings a server and returns the result."),
            ("/credits", "Displays the credits for the bot."),
            ("/shop", "Displays a joke menu of snacks."),
            ("/developersite", "Sends a link to the developer's website."),
            ("/discordsupportinvite", "Sends a link to the Discord support server."),
            ("/wave", "Waves at a user."),
            ("/hug", "Hugs a user."),
            ("/kiss", "Kisses a user."),
            ("/punch", "Punches a user."),
            ("/kick", "Kicks a user."),
            ("/banhammer", "Uses the banhammer on a user."),
            ("/marry", "Proposes to a user."),
            ("/divorce", "Divorces a user."),
            ("/slap", "Slaps a user."),
            ("/snatch", "Playfully snatches a user."),
            ("/triplebaka", "Sends a link to the Triple Baka video."),
            ("/spotify", "Sends a link to a Spotify playlist."),
            ("/coinflip", "Flips a coin by picking heads or tails."),
            ("/rps", "Plays Rock, Paper, Scissors with the bot.")
        ]
        for name, desc in commands_list:
            embed.add_field(name=name, value=desc, inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="credits", description="Displays the credits for the bot.")
    async def credits(self, interaction: discord.Interaction):
        # Try to get the current git commit hash
        try:
            commit_hash = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()
        except Exception:
            commit_hash = "Unknown"

        embed = discord.Embed(
            title="Bot Credits",
            description="This bot was developed with contributions from the following:",
            color=discord.Color.gold()
        )
        embed.add_field(name="Developer", value="zacarias posey - https://staffteam.learnhelp.cc/zac.html", inline=False)
        embed.add_field(name="Contributors", value="Izzy - https://staffteam.learnhelp.cc/izzy.html", inline=False)
        embed.add_field(name="Contributors", value="Milly - https://staffteam.learnhelp.cc/milly.html", inline=False)
        embed.add_field(name="Contributors", value="Slipstream - https://github.com/Slipstreamm", inline=False)
        embed.add_field(name="Powered By", value="Gemini, Discord API, The OpenStudio project, Learnhelp API", inline=False)
        embed.add_field(name="Website", value="https://discordbot.learnhelp.cc", inline=False)
        embed.add_field(name="Discord Server", value="https://discord.gg/9CFwFRPNH4", inline=False)
        embed.add_field(name="GitLab", value="https://gitlab.com/pancakes1234/wdiscordbotserver/-/tree/main", inline=False)
        embed.add_field(name="Version", value=f"Official Server Bot Version\nCommit Hash: [{commit_hash}](https://gitlab.com/pancakes1234/wdiscordbotserver/-/commit/{commit_hash})")
        embed.set_footer(text="Thank you for using the bot!")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="temps", description="Runs the 'sensors' command and sends its output to chat.")
    async def temps(self, interaction: discord.Interaction):
        """Executes the sensors command and returns the output."""
        try:
            # Run the 'sensors' command asynchronously
            process = await asyncio.create_subprocess_exec(
                "sensors",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            # Get the command output: prefer stdout, fallback to stderr if needed.
            output = stdout.decode("utf-8").strip() or stderr.decode("utf-8").strip() or "No output."
        except Exception as e:
            output = f"Error executing sensors command: {e}"

        # If the output is too long for a single message, send it as a file.
        if len(output) > 1900:  # leave some room for Discord formatting
            file_name = "temps.txt"
            with open(file_name, "w") as f:
                f.write(output)
            await interaction.response.send_message("Output was too long; see attached file:", file=discord.File(file_name))
        else:
            # Send output wrapped in a code block for clarity.
            await interaction.response.send_message(f"```\n{output}\n```")

    @app_commands.command(name="discordsupportinvite", description="Send a link to the Discord support server.")
    async def discordsupportinvite(self, interaction: discord.Interaction):
        await interaction.response.send_message("https://discord.gg/9CFwFRPNH4")

    @app_commands.command(name="developersite", description="Sends a link to the developer's website.")
    async def developersite(self, interaction: discord.Interaction):
        await interaction.response.send_message("https://discordbot.learnhelp.cc/")

    @app_commands.command(name="supportserver", description="Sends a link to the support server.")
    async def supportserver(self, interaction: discord.Interaction):
        await interaction.response.send_message("https://discord.gg/9CFwFRPNH4")

    @app_commands.command(name="contactsupport", description="support emails")
    async def contactsupport(self, interaction: discord.Interaction):
        await interaction.response.send_message("For general support, please email:help@learnhelp,cc\nFor security issues, please email:securityoffice@auditoffice.learnhelp.cc\nFor staff issues, please email:contact@admin.office.learnhelp.cc")


async def setup(bot: commands.Bot):
    await bot.add_cog(Core(bot))
