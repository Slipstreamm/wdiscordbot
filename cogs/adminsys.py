import discord
from discord.ext import commands
from discord import app_commands
import subprocess
import asyncio
import os
import tempfile
import json
import sys
import shutil
from typing import Optional, List, Tuple

class AdminSysCog(commands.Cog):
    """
    System administration cog with elevated privileges.
    Restricted to a specific user ID for security.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.authorized_user_id = 452666956353503252
        self.log_file = "admin_commands.log"
        print(f"AdminSysCog initialized. Authorized user ID: {self.authorized_user_id}")

    async def is_authorized_user(self, interaction: discord.Interaction) -> bool:
        """Check if the user is authorized to use admin commands."""
        if interaction.user.id != self.authorized_user_id:
            await interaction.response.send_message(
                "You are not authorized to use this command.",
                ephemeral=True
            )
            return False
        return True

    async def log_command(self, interaction: discord.Interaction, command_name: str, args: str = "") -> None:
        """Log command usage for security and auditing purposes."""
        timestamp = discord.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] User: {interaction.user} (ID: {interaction.user.id}) | Command: {command_name} | Args: {args}\n"

        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error logging admin command: {e}")

    async def run_command(self, command: str, use_sudo: bool = False) -> Tuple[str, str, int]:
        """
        Run a shell command and return its output.

        Args:
            command: The command to execute
            use_sudo: Whether to prefix the command with sudo

        Returns:
            Tuple of (stdout, stderr, return_code)
        """
        if use_sudo:
            command = f"sudo {command}"

        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            return (
                stdout.decode("utf-8", errors="replace").strip(),
                stderr.decode("utf-8", errors="replace").strip(),
                process.returncode
            )
        except Exception as e:
            return "", f"Error executing command: {str(e)}", 1

    async def send_response(self, interaction: discord.Interaction, content: str, ephemeral: bool = False) -> None:
        """
        Send a response, handling large outputs by splitting or sending as a file.

        Args:
            interaction: The interaction to respond to
            content: The content to send
            ephemeral: Whether the response should be ephemeral
        """
        if not content:
            content = "Command executed with no output."

        if len(content) <= 1990:
            # Send directly if content is small enough
            await interaction.followup.send(f"```\n{content}\n```", ephemeral=ephemeral)
        elif len(content) <= 50000:
            # Split into chunks if medium size
            chunks = [content[i:i+1990] for i in range(0, len(content), 1990)]
            for i, chunk in enumerate(chunks):
                await interaction.followup.send(
                    f"```\n{chunk}\n```" + (f" (Part {i+1}/{len(chunks)})" if len(chunks) > 1 else ""),
                    ephemeral=ephemeral
                )
        else:
            # Send as file if very large
            with tempfile.NamedTemporaryFile(mode="w+", suffix=".txt", delete=False) as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(content)

            await interaction.followup.send(
                "Output is too large. See attached file:",
                file=discord.File(temp_file_path),
                ephemeral=ephemeral
            )

            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except Exception:
                pass

    # Command Groups
    pkg_group = app_commands.Group(name="pkg", description="Package management commands")
    file_group = app_commands.Group(name="file", description="File operation commands")
    sys_group = app_commands.Group(name="sys", description="System administration commands")
    service_group = app_commands.Group(name="service", description="Service management commands")
    net_group = app_commands.Group(name="net", description="Network-related commands")

    # Package Management Commands
    @pkg_group.command(name="pip_install", description="Install a Python package using pip")
    @app_commands.describe(package="The package name to install")
    async def pip_install(self, interaction: discord.Interaction, package: str):
        """Install a Python package using pip."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "pip_install", package)

        stdout, stderr, return_code = await self.run_command(f"pip install {package}")

        if return_code == 0:
            await self.send_response(interaction, f"Successfully installed {package}\n\n{stdout}", ephemeral=True)
        else:
            await self.send_response(interaction, f"Failed to install {package}\n\n{stderr}", ephemeral=True)

    @pkg_group.command(name="pip_uninstall", description="Uninstall a Python package using pip")
    @app_commands.describe(package="The package name to uninstall")
    async def pip_uninstall(self, interaction: discord.Interaction, package: str):
        """Uninstall a Python package using pip."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "pip_uninstall", package)

        stdout, stderr, return_code = await self.run_command(f"pip uninstall -y {package}")

        if return_code == 0:
            await self.send_response(interaction, f"Successfully uninstalled {package}\n\n{stdout}", ephemeral=True)
        else:
            await self.send_response(interaction, f"Failed to uninstall {package}\n\n{stderr}", ephemeral=True)

    @pkg_group.command(name="pip_list", description="List installed Python packages")
    async def pip_list(self, interaction: discord.Interaction):
        """List installed Python packages."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "pip_list")

        stdout, stderr, return_code = await self.run_command("pip list")

        if return_code == 0:
            await self.send_response(interaction, stdout, ephemeral=True)
        else:
            await self.send_response(interaction, f"Failed to list packages\n\n{stderr}", ephemeral=True)

    @pkg_group.command(name="apt_install", description="Install a package using apt")
    @app_commands.describe(package="The package name to install")
    async def apt_install(self, interaction: discord.Interaction, package: str):
        """Install a package using apt."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "apt_install", package)

        stdout, stderr, return_code = await self.run_command(f"apt-get install -y {package}", use_sudo=True)

        if return_code == 0:
            await self.send_response(interaction, f"Successfully installed {package}\n\n{stdout}", ephemeral=True)
        else:
            await self.send_response(interaction, f"Failed to install {package}\n\n{stderr}", ephemeral=True)

    @pkg_group.command(name="apt_remove", description="Remove a package using apt")
    @app_commands.describe(package="The package name to remove")
    async def apt_remove(self, interaction: discord.Interaction, package: str):
        """Remove a package using apt."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "apt_remove", package)

        stdout, stderr, return_code = await self.run_command(f"apt-get remove -y {package}", use_sudo=True)

        if return_code == 0:
            await self.send_response(interaction, f"Successfully removed {package}\n\n{stdout}", ephemeral=True)
        else:
            await self.send_response(interaction, f"Failed to remove {package}\n\n{stderr}", ephemeral=True)

    @pkg_group.command(name="apt_update", description="Update package lists using apt")
    async def apt_update(self, interaction: discord.Interaction):
        """Update package lists using apt."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "apt_update")

        stdout, stderr, return_code = await self.run_command("apt-get update", use_sudo=True)

        if return_code == 0:
            await self.send_response(interaction, stdout, ephemeral=True)
        else:
            await self.send_response(interaction, f"Failed to update package lists\n\n{stderr}", ephemeral=True)

    @pkg_group.command(name="apt_upgrade", description="Upgrade packages using apt")
    async def apt_upgrade(self, interaction: discord.Interaction):
        """Upgrade packages using apt."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "apt_upgrade")

        stdout, stderr, return_code = await self.run_command("apt-get upgrade -y", use_sudo=True)

        if return_code == 0:
            await self.send_response(interaction, stdout, ephemeral=True)
        else:
            await self.send_response(interaction, f"Failed to upgrade packages\n\n{stderr}", ephemeral=True)

    # File Operation Commands
    @file_group.command(name="read", description="Read a file")
    @app_commands.describe(path="The path to the file to read")
    async def read_file(self, interaction: discord.Interaction, path: str):
        """Read a file and display its contents."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "read_file", path)

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()

            await self.send_response(interaction, f"Contents of {path}:\n\n{content}", ephemeral=True)
        except Exception as e:
            await self.send_response(interaction, f"Error reading file {path}: {str(e)}", ephemeral=True)

    @file_group.command(name="write", description="Write content to a file")
    @app_commands.describe(
        path="The path to the file to write",
        content="The content to write to the file"
    )
    async def write_file(self, interaction: discord.Interaction, path: str, content: str):
        """Write content to a file."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "write_file", f"{path} (content length: {len(content)})")

        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            await self.send_response(interaction, f"Successfully wrote to {path}", ephemeral=True)
        except Exception as e:
            await self.send_response(interaction, f"Error writing to file {path}: {str(e)}", ephemeral=True)

    @file_group.command(name="append", description="Append content to a file")
    @app_commands.describe(
        path="The path to the file to append to",
        content="The content to append to the file"
    )
    async def append_file(self, interaction: discord.Interaction, path: str, content: str):
        """Append content to a file."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "append_file", f"{path} (content length: {len(content)})")

        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)

            await self.send_response(interaction, f"Successfully appended to {path}", ephemeral=True)
        except Exception as e:
            await self.send_response(interaction, f"Error appending to file {path}: {str(e)}", ephemeral=True)

    @file_group.command(name="list", description="List files in a directory")
    @app_commands.describe(path="The directory path to list")
    async def list_files(self, interaction: discord.Interaction, path: str = "."):
        """List files in a directory."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "list_files", path)

        try:
            files = os.listdir(path)
            file_info = []

            for file in files:
                full_path = os.path.join(path, file)
                try:
                    stats = os.stat(full_path)
                    size = stats.st_size
                    is_dir = os.path.isdir(full_path)
                    file_info.append(f"{'📁' if is_dir else '📄'} {file} ({size} bytes)")
                except Exception:
                    file_info.append(f"? {file} (error getting info)")

            if file_info:
                await self.send_response(interaction, f"Contents of {path}:\n\n" + "\n".join(file_info), ephemeral=True)
            else:
                await self.send_response(interaction, f"Directory {path} is empty", ephemeral=True)
        except Exception as e:
            await self.send_response(interaction, f"Error listing directory {path}: {str(e)}", ephemeral=True)

    # System Commands
    @sys_group.command(name="exec", description="Execute a shell command")
    @app_commands.describe(
        command="The command to execute",
        use_sudo="Whether to use sudo"
    )
    async def execute_command(self, interaction: discord.Interaction, command: str, use_sudo: bool = False):
        """Execute a shell command."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "execute_command", f"{command} (sudo: {use_sudo})")

        stdout, stderr, return_code = await self.run_command(command, use_sudo)

        output = f"Command: {command}\nReturn Code: {return_code}\n\n"
        if stdout:
            output += f"STDOUT:\n{stdout}\n\n"
        if stderr:
            output += f"STDERR:\n{stderr}"

        await self.send_response(interaction, output, ephemeral=True)

    @sys_group.command(name="info", description="Display system information")
    async def system_info(self, interaction: discord.Interaction):
        """Display system information."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "system_info")

        # Get various system information
        commands = [
            ("OS Information", "cat /etc/os-release"),
            ("Kernel Version", "uname -a"),
            ("CPU Information", "lscpu"),
            ("Memory Usage", "free -h"),
            ("Disk Usage", "df -h"),
            ("Uptime", "uptime")
        ]

        results = []
        for title, cmd in commands:
            stdout, stderr, return_code = await self.run_command(cmd)
            if return_code == 0:
                results.append(f"=== {title} ===\n{stdout}")
            else:
                results.append(f"=== {title} ===\nError: {stderr}")

        await self.send_response(interaction, "\n\n".join(results), ephemeral=True)

    @sys_group.command(name="processes", description="List running processes")
    @app_commands.describe(
        filter="Optional filter string to search for specific processes"
    )
    async def list_processes(self, interaction: discord.Interaction, filter: str = ""):
        """List running processes, optionally filtered."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "list_processes", filter)

        command = "ps aux"
        if filter:
            command += f" | grep -i {filter}"

        stdout, stderr, return_code = await self.run_command(command)

        if return_code == 0 and stdout:
            await self.send_response(interaction, stdout, ephemeral=True)
        else:
            await self.send_response(interaction, f"No processes found or error occurred: {stderr}", ephemeral=True)

    @sys_group.command(name="kill", description="Kill a process by PID")
    @app_commands.describe(
        pid="Process ID to kill",
        signal="Signal to send (default: 15/SIGTERM)"
    )
    async def kill_process(self, interaction: discord.Interaction, pid: int, signal: int = 15):
        """Kill a process by its PID."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "kill_process", f"PID: {pid}, Signal: {signal}")

        _, stderr, return_code = await self.run_command(f"kill -{signal} {pid}", use_sudo=True)

        if return_code == 0:
            await self.send_response(interaction, f"Successfully sent signal {signal} to process {pid}", ephemeral=True)
        else:
            await self.send_response(interaction, f"Failed to kill process {pid}: {stderr}", ephemeral=True)

    @sys_group.command(name="disk", description="Show disk usage information")
    async def disk_usage(self, interaction: discord.Interaction):
        """Show detailed disk usage information."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "disk_usage")

        commands = [
            ("Disk Usage", "df -h"),
            ("Disk I/O Statistics", "iostat -x 1 2 | tail -n +4"),
            ("Largest Directories", "du -h --max-depth=1 / 2>/dev/null | sort -hr | head -n 10")
        ]

        results = []
        for title, cmd in commands:
            stdout, stderr, return_code = await self.run_command(cmd)
            if return_code == 0 and stdout:
                results.append(f"=== {title} ===\n{stdout}")
            else:
                results.append(f"=== {title} ===\nError or no output: {stderr}")

        await self.send_response(interaction, "\n\n".join(results), ephemeral=True)

    @sys_group.command(name="env", description="View or set environment variables")
    @app_commands.describe(
        variable="Environment variable name (leave empty to list all)",
        value="New value (leave empty to just view the variable)"
    )
    async def environment(self, interaction: discord.Interaction, variable: str = "", value: str = ""):
        """View or set environment variables."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)

        if not variable:
            # List all environment variables
            await self.log_command(interaction, "environment", "list all")
            stdout, stderr, return_code = await self.run_command("env | sort")

            if return_code == 0:
                await self.send_response(interaction, stdout, ephemeral=True)
            else:
                await self.send_response(interaction, f"Failed to list environment variables: {stderr}", ephemeral=True)
        elif not value:
            # View a specific environment variable
            await self.log_command(interaction, "environment", f"view {variable}")
            stdout, stderr, return_code = await self.run_command(f"echo ${variable}")

            if return_code == 0:
                await self.send_response(interaction, f"{variable}={stdout}", ephemeral=True)
            else:
                await self.send_response(interaction, f"Failed to get environment variable: {stderr}", ephemeral=True)
        else:
            # Set an environment variable
            await self.log_command(interaction, "environment", f"set {variable}={value}")

            # Write to .env file if it exists
            env_file = ".env"
            if os.path.exists(env_file):
                try:
                    # Read current .env file
                    with open(env_file, "r") as f:
                        lines = f.readlines()

                    # Check if variable already exists
                    var_exists = False
                    for i, line in enumerate(lines):
                        if line.startswith(f"{variable}="):
                            lines[i] = f"{variable}={value}\n"
                            var_exists = True
                            break

                    # Add variable if it doesn't exist
                    if not var_exists:
                        lines.append(f"{variable}={value}\n")

                    # Write back to .env file
                    with open(env_file, "w") as f:
                        f.writelines(lines)

                    await self.send_response(interaction,
                        f"Environment variable {variable} set to {value} in {env_file}. "
                        f"Note: This will take effect after bot restart.",
                        ephemeral=True
                    )
                except Exception as e:
                    await self.send_response(interaction, f"Error updating .env file: {str(e)}", ephemeral=True)
            else:
                await self.send_response(interaction,
                    f"No .env file found. Cannot persist environment variable.",
                    ephemeral=True
                )

    # Service Management Commands
    @service_group.command(name="status", description="Check the status of a service")
    @app_commands.describe(service="The name of the service to check")
    async def service_status(self, interaction: discord.Interaction, service: str):
        """Check the status of a system service."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "service_status", service)

        stdout, stderr, return_code = await self.run_command(f"systemctl status {service}", use_sudo=True)

        if return_code == 0 or return_code == 3:  # 3 is returned when service is stopped but exists
            await self.send_response(interaction, stdout, ephemeral=True)
        else:
            await self.send_response(interaction, f"Error checking service status: {stderr}", ephemeral=True)

    @service_group.command(name="start", description="Start a service")
    @app_commands.describe(service="The name of the service to start")
    async def service_start(self, interaction: discord.Interaction, service: str):
        """Start a system service."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "service_start", service)

        _, stderr, return_code = await self.run_command(f"systemctl start {service}", use_sudo=True)

        if return_code == 0:
            # Get the status after starting
            status_stdout, _, _ = await self.run_command(f"systemctl status {service}", use_sudo=True)
            await self.send_response(interaction, f"Service {service} started successfully.\n\n{status_stdout}", ephemeral=True)
        else:
            await self.send_response(interaction, f"Failed to start service {service}: {stderr}", ephemeral=True)

    @service_group.command(name="stop", description="Stop a service")
    @app_commands.describe(service="The name of the service to stop")
    async def service_stop(self, interaction: discord.Interaction, service: str):
        """Stop a system service."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "service_stop", service)

        _, stderr, return_code = await self.run_command(f"systemctl stop {service}", use_sudo=True)

        if return_code == 0:
            await self.send_response(interaction, f"Service {service} stopped successfully.", ephemeral=True)
        else:
            await self.send_response(interaction, f"Failed to stop service {service}: {stderr}", ephemeral=True)

    @service_group.command(name="restart", description="Restart a service")
    @app_commands.describe(service="The name of the service to restart")
    async def service_restart(self, interaction: discord.Interaction, service: str):
        """Restart a system service."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "service_restart", service)

        _, stderr, return_code = await self.run_command(f"systemctl restart {service}", use_sudo=True)

        if return_code == 0:
            # Get the status after restarting
            status_stdout, _, _ = await self.run_command(f"systemctl status {service}", use_sudo=True)
            await self.send_response(interaction, f"Service {service} restarted successfully.\n\n{status_stdout}", ephemeral=True)
        else:
            await self.send_response(interaction, f"Failed to restart service {service}: {stderr}", ephemeral=True)

    @service_group.command(name="list", description="List all services")
    @app_commands.describe(
        filter="Optional filter string to search for specific services",
        show_all="Show all services, including inactive ones"
    )
    async def service_list(self, interaction: discord.Interaction, filter: str = "", show_all: bool = False):
        """List system services, optionally filtered."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "service_list", f"filter: {filter}, show_all: {show_all}")

        command = "systemctl list-units --type=service"
        if show_all:
            command += " --all"
        if filter:
            command += f" | grep -i {filter}"

        stdout, stderr, return_code = await self.run_command(command, use_sudo=True)

        if return_code == 0 and stdout:
            await self.send_response(interaction, stdout, ephemeral=True)
        else:
            await self.send_response(interaction, f"No services found or error occurred: {stderr}", ephemeral=True)

    # Network Commands
    @net_group.command(name="ping", description="Ping a host")
    @app_commands.describe(
        host="The host to ping",
        count="Number of packets to send (default: 4)"
    )
    async def ping_host(self, interaction: discord.Interaction, host: str, count: int = 4):
        """Ping a host to check connectivity."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "ping_host", f"{host} (count: {count})")

        stdout, stderr, return_code = await self.run_command(f"ping -c {count} {host}")

        if return_code == 0:
            await self.send_response(interaction, stdout, ephemeral=True)
        else:
            await self.send_response(interaction, f"Failed to ping {host}: {stderr}", ephemeral=True)

    @net_group.command(name="ifconfig", description="Show network interface configuration")
    @app_commands.describe(interface="Optional specific interface to show")
    async def ifconfig(self, interaction: discord.Interaction, interface: str = ""):
        """Show network interface configuration."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "ifconfig", interface)

        command = "ifconfig"
        if interface:
            command += f" {interface}"

        stdout, stderr, return_code = await self.run_command(command)

        if return_code == 0:
            await self.send_response(interaction, stdout, ephemeral=True)
        else:
            # Try ip addr as fallback
            stdout, stderr, return_code = await self.run_command("ip addr")
            if return_code == 0:
                await self.send_response(interaction, stdout, ephemeral=True)
            else:
                await self.send_response(interaction, f"Failed to get network interface info: {stderr}", ephemeral=True)

    @net_group.command(name="netstat", description="Show network statistics")
    @app_commands.describe(
        option="Options for netstat (e.g., 'tuln' for TCP, UDP, listening, numeric)"
    )
    async def netstat(self, interaction: discord.Interaction, option: str = "tuln"):
        """Show network statistics."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "netstat", option)

        stdout, stderr, return_code = await self.run_command(f"netstat -{option}")

        if return_code == 0:
            await self.send_response(interaction, stdout, ephemeral=True)
        else:
            # Try ss as fallback
            stdout, stderr, return_code = await self.run_command("ss -tuln")
            if return_code == 0:
                await self.send_response(interaction, stdout, ephemeral=True)
            else:
                await self.send_response(interaction, f"Failed to get network statistics: {stderr}", ephemeral=True)

    @net_group.command(name="traceroute", description="Trace the route to a host")
    @app_commands.describe(host="The host to trace the route to")
    async def traceroute(self, interaction: discord.Interaction, host: str):
        """Trace the route to a host."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "traceroute", host)

        stdout, stderr, return_code = await self.run_command(f"traceroute {host}")

        if return_code == 0:
            await self.send_response(interaction, stdout, ephemeral=True)
        else:
            await self.send_response(interaction, f"Failed to trace route to {host}: {stderr}", ephemeral=True)

    @net_group.command(name="dns", description="Perform DNS lookup")
    @app_commands.describe(
        host="The host to lookup",
        type="Record type (default: A)"
    )
    async def dns_lookup(self, interaction: discord.Interaction, host: str, type: str = "A"):
        """Perform DNS lookup for a host."""
        if not await self.is_authorized_user(interaction):
            return

        await interaction.response.defer(ephemeral=True)
        await self.log_command(interaction, "dns_lookup", f"{host} (type: {type})")

        stdout, stderr, return_code = await self.run_command(f"dig {host} {type}")

        if return_code == 0:
            await self.send_response(interaction, stdout, ephemeral=True)
        else:
            # Try nslookup as fallback
            stdout, stderr, return_code = await self.run_command(f"nslookup -type={type} {host}")
            if return_code == 0:
                await self.send_response(interaction, stdout, ephemeral=True)
            else:
                await self.send_response(interaction, f"Failed to perform DNS lookup for {host}: {stderr}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminSysCog(bot))
    print("AdminSysCog has been loaded.")
