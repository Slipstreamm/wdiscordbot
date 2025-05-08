import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import traceback
import sys
import functools
from discord import app_commands

# Load environment variables
load_dotenv()
discord_token = os.getenv("DISCORD_TOKEN")

# Ensure token is set
if not discord_token:
    raise ValueError("Missing DISCORD_TOKEN environment variable.")

# Configure bot with intents
intents = discord.Intents.default()
intents.message_content = True

# Technically no reason to have a prefix set because the bot only uses slash commands.
bot = commands.Bot(command_prefix="/", intents=intents)

# User ID to send error notifications to
ERROR_NOTIFICATION_USER_ID = 452666956353503252

# Decorator to catch and report exceptions in any function
def catch_exceptions(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            # Get traceback
            tb_string = "".join(traceback.format_exception(type(e), e, e.__traceback__))

            # Log to console
            print(f"Uncaught exception in {func.__name__}:")
            print(tb_string)

            # Context information
            context = f"Function: {func.__name__}, Module: {func.__module__}"
            if args and hasattr(args[0], '__class__'):
                context += f", Class: {args[0].__class__.__name__}"

            # Get the bot instance to send the error
            # This assumes the function is a method of a cog with a bot attribute
            # or the first argument is the bot itself
            bot_instance = None
            if args and hasattr(args[0], 'bot'):
                bot_instance = args[0].bot
            elif args and isinstance(args[0], commands.Bot):
                bot_instance = args[0]

            if bot_instance:
                # Use the global bot instance's send_error_dm function
                user = await bot_instance.fetch_user(ERROR_NOTIFICATION_USER_ID)
                if user:
                    error_content = f"**Error Type:** {type(e).__name__}\n"
                    error_content += f"**Error Message:** {str(e)}\n"
                    error_content += f"**Context:** {context}\n"

                    if tb_string:
                        if len(tb_string) > 1500:
                            tb_string = tb_string[:1500] + "...(truncated)"
                        error_content += f"**Traceback:**\n```\n{tb_string}\n```"

                    await user.send(error_content)

            # Re-raise the exception to maintain the original behavior
            raise
    return wrapper

# Load cog files dynamically
async def load_cogs():
    for filename in os.listdir("cogs/"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded cog: {filename}")
            except Exception as e:
                print(f"Failed to load cog {filename}: {e}")

                # Send DM notification for cog loading error
                tb_string = "".join(traceback.format_exception(type(e), e, e.__traceback__))
                try:
                    await send_error_dm(
                        error_type=type(e).__name__,
                        error_message=str(e),
                        error_traceback=tb_string,
                        context_info=f"Error loading cog: {filename}"
                    )
                except Exception as dm_error:
                    print(f"Failed to send error DM for cog loading error: {dm_error}")

async def send_error_dm(error_type, error_message, error_traceback=None, context_info=None):
    """Send error details to the specified user via DM."""
    try:
        # Get the user to send the error to
        user = await bot.fetch_user(ERROR_NOTIFICATION_USER_ID)
        if not user:
            print(f"Could not find user with ID {ERROR_NOTIFICATION_USER_ID} to send error notification")
            return

        # Format the error message
        error_content = f"**Error Type:** {error_type}\n"
        error_content += f"**Error Message:** {error_message}\n"

        if context_info:
            error_content += f"**Context:** {context_info}\n"

        # Add traceback if available (might need to be split into multiple messages if too long)
        if error_traceback:
            # Limit traceback length to avoid hitting Discord's message limit
            if len(error_traceback) > 1500:
                error_traceback = error_traceback[:1500] + "...(truncated)"
            error_content += f"**Traceback:**\n```\n{error_traceback}\n```"

        # Send the DM
        await user.send(error_content)
    except Exception as e:
        # If we can't send the DM, at least log it to console
        print(f"Failed to send error DM: {e}")

@bot.event
async def on_error(event, *args, **kwargs):
    """Global error handler for all events."""
    # Get the exception info
    error_type, error_value, error_traceback = sys.exc_info()
    tb_string = "".join(traceback.format_exception(error_type, error_value, error_traceback))

    # Log to console
    print(f"Error in event {event}:")
    print(tb_string)

    # Context information
    context = f"Event: {event}"
    if args:
        context += f", Args: {args}"
    if kwargs:
        context += f", Kwargs: {kwargs}"

    # Send DM notification
    await send_error_dm(
        error_type=error_type.__name__,
        error_message=str(error_value),
        error_traceback=tb_string,
        context_info=context
    )

@bot.event
async def on_command_error(ctx, error):
    """Error handler for prefix commands."""
    # Get the original error if it's wrapped in CommandInvokeError
    error = getattr(error, 'original', error)

    # Get traceback
    tb_string = "".join(traceback.format_exception(type(error), error, error.__traceback__))

    # Log to console
    print(f"Command error in {ctx.command}:")
    print(tb_string)

    # Context information
    context = f"Command: {ctx.command}, Author: {ctx.author} ({ctx.author.id}), Guild: {ctx.guild.name if ctx.guild else 'DM'} ({ctx.guild.id if ctx.guild else 'N/A'}), Channel: {ctx.channel}"

    # Send DM notification
    await send_error_dm(
        error_type=type(error).__name__,
        error_message=str(error),
        error_traceback=tb_string,
        context_info=context
    )

    # You can still respond to the user if appropriate
    try:
        await ctx.send(f"An error occurred while executing the command. The bot owner has been notified.")
    except:
        pass

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    """Error handler for application (slash) commands."""
    # Get the original error if it's wrapped
    error = getattr(error, 'original', error)

    # Get traceback
    tb_string = "".join(traceback.format_exception(type(error), error, error.__traceback__))

    # Log to console
    command_name = interaction.command.name if interaction.command else "Unknown"
    print(f"App command error in {command_name}:")
    print(tb_string)

    # Context information
    context = f"Command: {command_name}, Author: {interaction.user} ({interaction.user.id}), Guild: {interaction.guild.name if interaction.guild else 'DM'} ({interaction.guild.id if interaction.guild else 'N/A'}), Channel: {interaction.channel}"

    # Send DM notification
    await send_error_dm(
        error_type=type(error).__name__,
        error_message=str(error),
        error_traceback=tb_string,
        context_info=context
    )

    # Respond to the interaction if it hasn't been responded to yet
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message("An error occurred while executing the command. The bot owner has been notified.", ephemeral=True)
        else:
            await interaction.followup.send("An error occurred while executing the command. The bot owner has been notified.", ephemeral=True)
    except:
        pass

@bot.event
async def on_ready():
    try:
        await bot.tree.sync()  # Sync commands globally or specify a guild if needed
        print("Commands synced successfully!")
    except Exception as e:
        print(f"Failed to sync commands: {e}")

        # Send DM notification for sync error
        tb_string = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        await send_error_dm(
            error_type=type(e).__name__,
            error_message=str(e),
            error_traceback=tb_string,
            context_info="Error occurred during command sync in on_ready event"
        )

    print(f"Logged in as {bot.user}")
    print(f"Global error handling is active - errors will be sent to user ID: {ERROR_NOTIFICATION_USER_ID}")

# Test commands to verify error handling
@bot.command(name="testerror")
async def test_error(ctx):
    """Test command to verify error handling by intentionally raising an exception."""
    # Use ctx to avoid the unused variable warning
    await ctx.send(f"Testing error handling in {ctx.command}...")
    raise ValueError("This is a test error to verify error handling")

@bot.tree.command(name="testerror", description="Test slash command to verify error handling")
async def test_error_slash(interaction: discord.Interaction):
    """Test slash command to verify error handling by intentionally raising an exception."""
    await interaction.response.send_message("Testing error handling in slash command...")
    raise ValueError("This is a test error to verify slash command error handling")

async def main():
    async with bot:
        await load_cogs()
        await bot.start(discord_token)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        # Handle startup errors
        print(f"Critical error during bot startup: {e}")
        tb_string = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        print(tb_string)

        # We can't use the async function here since the bot isn't running
        print(f"Could not send error notification to user ID {ERROR_NOTIFICATION_USER_ID} - bot not running")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print(f"Traceback: {tb_string}")
