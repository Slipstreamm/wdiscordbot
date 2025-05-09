import discord
from discord.ext import commands
from discord import app_commands
import subprocess
import sys

class Shell(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='shell', aliases=['exec', 'cmd'])
    @commands.is_owner()
    async def shell_command(self, ctx, *, command: str):
        """Executes a shell command (Owner only)."""
        try:
            # Execute the command
            process = subprocess.run(
                command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, # Decode stdout/stderr as text
                encoding='utf-8' # Specify encoding
            )
            stdout = process.stdout
            stderr = process.stderr

            output = ""
            if stdout:
                output += f"**Stdout:**\n```\n{stdout}\n```"
            if stderr:
                output += f"**Stderr:**\n```\n{stderr}\n```"

            if not output:
                output = "Command executed successfully with no output."

            # Send output, splitting if necessary due to Discord message length limits
            if len(output) > 2000:
                # Split output into chunks
                chunks = [output[i:i+1990] for i in range(0, len(output), 1990)]
                for chunk in chunks:
                    await ctx.send(chunk)
            else:
                await ctx.send(output)

        except subprocess.CalledProcessError as e:
            await ctx.send(f"**Error executing command:**\n```\n{e}\n```\n**Stderr:**\n```\n{e.stderr}\n```")
        except Exception as e:
            await ctx.send(f"An unexpected error occurred: ```\n{e}\n```")

    @app_commands.command(name='shell_app', description='Executes a shell command (Owner only).')
    @app_commands.describe(command='The shell command to execute')
    @app_commands.is_owner()
    async def shell_app_command(self, interaction: discord.Interaction, command: str):
        """Executes a shell command using application commands (Owner only)."""
        await interaction.response.defer() # Defer the response as command execution might take time
        try:
            # Execute the command
            process = subprocess.run(
                command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True, # Decode stdout/stderr as text
                encoding='utf-8' # Specify encoding
            )
            stdout = process.stdout
            stderr = process.stderr

            output = ""
            if stdout:
                output += f"**Stdout:**\n```\n{stdout}\n```"
            if stderr:
                output += f"**Stderr:**\n```\n{stderr}\n```"

            if not output:
                output = "Command executed successfully with no output."

            # Send output, splitting if necessary due to Discord message length limits
            if len(output) > 2000:
                # Split output into chunks
                chunks = [output[i:i+1990] for i in range(0, len(output), 1990)]
                for chunk in chunks:
                    await interaction.followup.send(chunk)
            else:
                await interaction.followup.send(output)

        except subprocess.CalledProcessError as e:
            await interaction.followup.send(f"**Error executing command:**\n```\n{e}\n```\n**Stderr:**\n```\n{e.stderr}\n```")
        except Exception as e:
            await interaction.followup.send(f"An unexpected error occurred: ```\n{e}\n```")


async def setup(bot):
    await bot.add_cog(Shell(bot))
