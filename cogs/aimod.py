# moderation_cog.py
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp # For making asynchronous HTTP requests
import json
import os # To load environment variables
import collections # For deque
import datetime # For timestamps
import io # For BytesIO operations
import base64 # For encoding images to base64
from PIL import Image # For image processing
import cv2 # For video processing
import numpy as np # For array operations
import tempfile # For temporary file operations

# --- Configuration ---
# The OpenRouter API key will be loaded from environment variable
OPENROUTER_API_KEY_ENV_VAR = "SLIPSTREAM_OPENROUTER_KEY"
OPENROUTER_API_KEY = os.getenv(OPENROUTER_API_KEY_ENV_VAR)  # Load directly from environment

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODEL = "google/gemini-2.5-flash-preview-05-20" # Make sure this model is available via your OpenRouter key

# Environment variable for the authorization secret (still used for other API calls)
MOD_LOG_API_SECRET_ENV_VAR = "MOD_LOG_API_SECRET"

# --- Per-Guild Discord Configuration ---
GUILD_CONFIG_DIR = "/home/ubuntu/wdiscordbot-json-data" # Using the existing directory for all json data
GUILD_CONFIG_PATH = os.path.join(GUILD_CONFIG_DIR, "guild_config.json")
USER_INFRACTIONS_PATH = os.path.join(GUILD_CONFIG_DIR, "user_infractions.json")

os.makedirs(GUILD_CONFIG_DIR, exist_ok=True)

# Initialize Guild Config
if not os.path.exists(GUILD_CONFIG_PATH):
    with open(GUILD_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({}, f)
try:
    with open(GUILD_CONFIG_PATH, "r", encoding="utf-8") as f:
        GUILD_CONFIG = json.load(f)
except Exception as e:
    print(f"Failed to load per-guild config from {GUILD_CONFIG_PATH}: {e}")
    GUILD_CONFIG = {}

# Initialize User Infractions
if not os.path.exists(USER_INFRACTIONS_PATH):
    with open(USER_INFRACTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump({}, f) # Stores infractions as { "guild_id_user_id": [infraction_list] }
try:
    with open(USER_INFRACTIONS_PATH, "r", encoding="utf-8") as f:
        USER_INFRACTIONS = json.load(f)
except Exception as e:
    print(f"Failed to load user infractions from {USER_INFRACTIONS_PATH}: {e}")
    USER_INFRACTIONS = {}

def save_guild_config():
    try:
        # os.makedirs(os.path.dirname(GUILD_CONFIG_PATH), exist_ok=True) # Already created by GUILD_CONFIG_DIR
        # if not os.path.exists(GUILD_CONFIG_PATH): # Redundant check, file is created if not exists
        #     with open(GUILD_CONFIG_PATH, "w", encoding="utf-8") as f:
        #         json.dump({}, f)
        with open(GUILD_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(GUILD_CONFIG, f, indent=2)
    except Exception as e:
        print(f"Failed to save per-guild config: {e}")

def save_user_infractions():
    try:
        # os.makedirs(os.path.dirname(USER_INFRACTIONS_PATH), exist_ok=True) # Already created by GUILD_CONFIG_DIR
        # if not os.path.exists(USER_INFRACTIONS_PATH): # Redundant check
        #     with open(USER_INFRACTIONS_PATH, "w", encoding="utf-8") as f:
        #         json.dump({}, f)
        with open(USER_INFRACTIONS_PATH, "w", encoding="utf-8") as f:
            json.dump(USER_INFRACTIONS, f, indent=2)
    except Exception as e:
        print(f"Failed to save user infractions: {e}")

def get_guild_config(guild_id: int, key: str, default=None):
    guild_str = str(guild_id)
    if guild_str in GUILD_CONFIG and key in GUILD_CONFIG[guild_str]:
        return GUILD_CONFIG[guild_str][key]
    return default

def set_guild_config(guild_id: int, key: str, value):
    guild_str = str(guild_id)
    if guild_str not in GUILD_CONFIG:
        GUILD_CONFIG[guild_str] = {}
    GUILD_CONFIG[guild_str][key] = value
    save_guild_config()

def get_user_infraction_history(guild_id: int, user_id: int) -> list:
    """Retrieves a list of past infractions for a specific user in a guild."""
    key = f"{guild_id}_{user_id}"
    return USER_INFRACTIONS.get(key, [])

def add_user_infraction(guild_id: int, user_id: int, rule_violated: str, action_taken: str, reasoning: str, timestamp: str):
    """Adds a new infraction record for a user."""
    key = f"{guild_id}_{user_id}"
    if key not in USER_INFRACTIONS:
        USER_INFRACTIONS[key] = []

    infraction_record = {
        "timestamp": timestamp,
        "rule_violated": rule_violated,
        "action_taken": action_taken,
        "reasoning": reasoning
    }
    USER_INFRACTIONS[key].append(infraction_record)
    # Keep only the last N infractions to prevent the file from growing too large, e.g., last 10
    USER_INFRACTIONS[key] = USER_INFRACTIONS[key][-10:]
    save_user_infractions()

# Server rules to provide context to the AI
SERVER_RULES = """
# Server Rules

* **NSFW Content:**
The only rule regarding NSFW content is that **real-life pornography is strictly prohibited**, and you may **only post full-on pornographic images in designated NSFW channels**.
Explicit stickers and emojis are NOT considered "full-on pornographic images" and are always allowed in any channel.

* **Real-Life Pornography:** No real-life pornography is permitted.

* **Respectful Conduct & Edgy Humor:**
    * No harassment, hate speech (as defined by attacking protected groups), or genuine bullying.
    * *Context is key:* Edgy humor, dark jokes, and roasting are permitted and expected.
    * However, this does not excuse targeted, malicious personal attacks or harassment, especially if the recipient is clearly not okay with it.
    * If it stops being a "joke" and becomes genuine harassment, it's a rule violation.

* **No Discrimination:** Discrimination based on race, gender identity, sexual orientation, religion, nationality, disability, or other protected characteristics is prohibited.

* **AI-Generated Pornography:** Do not post AI-generated pornography.

* **Zero Tolerance for Pedophilia:** Any form of pedophilia, including lolicon and shotacon content, is strictly forbidden and will result in an immediate ban.

* **Channel Usage:** Please use channels for their intended purposes. Bot commands should primarily be used in `#bot-commands`, unless they are part of a bot-based game or event happening in another specific channel.

* **Gore:** Do not post gore or graphic real-life violence.

* **Suggestions:** We welcome your suggestions for the server! Please post them in the `#suggestions` channel.

---

**Reporting Violations:**
If you witness someone breaking these rules, please ping an `@Moderator` with details.

---

**Moderator Applications:**
Use the bot command `/modapp apply`
"""
SUICIDAL_HELP_RESOURCES = """
Hey, I'm really concerned to hear you're feeling this way. Please know that you're not alone and there are people who want to support you.
Your well-being is important to us on this server.

Here are some immediate resources that can offer help right now:

- **National Crisis and Suicide Lifeline (US):** Call or text **988**. This is available 24/7, free, and confidential.
- **Crisis Text Line (US):** Text **HOME** to **741741**. This is also a 24/7 free crisis counseling service.
- **The Trevor Project (for LGBTQ youth):** Call **1-866-488-7386** or visit their website for chat/text options: <https://www.thetrevorproject.org/get-help/>
- **The Jed Foundation (Mental Health Resource Center):** Provides resources for teens and young adults: <https://www.jedfoundation.org/>
- **Find A Helpline (International):** If you're outside the US, this site can help you find resources in your country: <https://findahelpline.com/>

Please reach out to one of these. We've also alerted our server's support team so they are aware and can offer a listening ear or further guidance if you're comfortable.
You matter, and help is available.
"""

class ModerationCog(commands.Cog):
    """
    A Discord Cog that uses OpenRouter AI to moderate messages based on server rules.
    Loads API key from the SLIPSTREAM_OPENROUTER_KEY environment variable.
    """
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Create a persistent session for making API requests
        self.session = aiohttp.ClientSession()
        self.openrouter_models = []
        self.last_ai_decisions = collections.deque(maxlen=5) # Store last 5 AI decisions
        # Initialize with the environment variable value
        self.openrouter_api_key = OPENROUTER_API_KEY
        # Supported image file extensions
        self.image_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
        # Supported animated file extensions
        self.gif_extensions = ['.gif']
        # Supported video file extensions
        self.video_extensions = ['.mp4', '.webm', '.mov']
        print("ModerationCog Initialized.")

    async def cog_load(self):
        """Loads OpenRouter models and the API key from environment variable when the cog is loaded."""
        print("ModerationCog cog_load started.")
        self._load_openrouter_models()

        # Load the OpenRouter API key from environment variable
        self.openrouter_api_key = os.getenv(OPENROUTER_API_KEY_ENV_VAR)

        if not self.openrouter_api_key:
            print("\n" + "="*60)
            print("=== WARNING: Failed to load OpenRouter API key from environment! ===")
            print("=== The Moderation Cog requires a valid API key to function. ===")
            print(f"=== Check the {OPENROUTER_API_KEY_ENV_VAR} environment variable. ===")
            print("="*60 + "\n")
        else:
            print(f"Successfully loaded OpenRouter API key from {OPENROUTER_API_KEY_ENV_VAR} environment variable.")
            print(f"OpenRouter API key loaded (length: {len(self.openrouter_api_key) if self.openrouter_api_key else 0}).")
        print("ModerationCog cog_load finished.")

    def _load_openrouter_models(self):
        """Loads OpenRouter model data from the JSON file."""
        models_json_path = "/home/ubuntu/wdiscordbot-internal-server-aws/data/openrouter_models.json" # Relative to bot's root
        try:
            if os.path.exists(models_json_path):
                with open(models_json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "data" in data and isinstance(data["data"], list):
                        for model_info in data["data"]:
                            if isinstance(model_info, dict) and "id" in model_info and "name" in model_info:
                                self.openrouter_models.append(
                                    {"id": model_info["id"], "name": model_info["name"]}
                                )
                        print(f"Successfully loaded {len(self.openrouter_models)} OpenRouter models for autocomplete.")
                    else:
                        print(f"Warning: {models_json_path} does not have the expected 'data' list structure.")
            else:
                print(f"Warning: {models_json_path} not found. AI_MODEL autocomplete will be empty.")
        except json.JSONDecodeError:
            print(f"Error: Could not decode JSON from {models_json_path}. AI_MODEL autocomplete will be empty.")
        except Exception as e:
            print(f"Error loading OpenRouter models from {models_json_path}: {e}. AI_MODEL autocomplete will be empty.")


    async def cog_unload(self):
        """Clean up the session when the cog is unloaded."""
        await self.session.close()
        print("ModerationCog Unloaded, session closed.")

    async def process_image(self, attachment: discord.Attachment) -> tuple[str, bytes]:
        """
        Process an image attachment and return its base64 encoding.

        Args:
            attachment: The Discord attachment containing the image

        Returns:
            Tuple of (mime_type, image_bytes)
        """
        try:
            # Download the image
            image_bytes = await attachment.read()
            mime_type = attachment.content_type or "image/jpeg"  # Default to jpeg if not specified

            # Return the image bytes and mime type
            return mime_type, image_bytes
        except Exception as e:
            print(f"Error processing image: {e}")
            return None, None

    async def process_gif(self, attachment: discord.Attachment) -> tuple[str, bytes]:
        """
        Process a GIF attachment and extract the first frame.

        Args:
            attachment: The Discord attachment containing the GIF

        Returns:
            Tuple of (mime_type, image_bytes) of the first frame
        """
        try:
            # Download the GIF
            gif_bytes = await attachment.read()

            # Open the GIF using PIL
            with Image.open(io.BytesIO(gif_bytes)) as gif:
                # Convert to RGB if needed
                if gif.mode != 'RGB':
                    first_frame = gif.convert('RGB')
                else:
                    first_frame = gif

                # Save the first frame to a bytes buffer
                output = io.BytesIO()
                first_frame.save(output, format='JPEG')
                output.seek(0)

                return "image/jpeg", output.getvalue()
        except Exception as e:
            print(f"Error processing GIF: {e}")
            return None, None

    async def process_attachment(self, attachment: discord.Attachment) -> tuple[str, bytes, str]:
        """
        Process any attachment and return the appropriate image data.

        Args:
            attachment: The Discord attachment

        Returns:
            Tuple of (mime_type, image_bytes, attachment_type)
            attachment_type is one of: 'image', 'gif', 'video', or None if unsupported
        """
        if not attachment:
            return None, None, None

        # Get the file extension
        filename = attachment.filename.lower()
        _, ext = os.path.splitext(filename)

        # Process based on file type
        if ext in self.image_extensions:
            mime_type, image_bytes = await self.process_image(attachment)
            return mime_type, image_bytes, 'image'
        elif ext in self.gif_extensions:
            mime_type, image_bytes = await self.process_gif(attachment)
            return mime_type, image_bytes, 'gif'
        elif ext in self.video_extensions:
            mime_type, image_bytes = await self.process_video(attachment)
            return mime_type, image_bytes, 'video'
        else:
            print(f"Unsupported file type: {ext}")
            return None, None, None

    async def process_video(self, attachment: discord.Attachment) -> tuple[str, bytes]:
        """
        Process a video attachment and extract the first frame.

        Args:
            attachment: The Discord attachment containing the video

        Returns:
            Tuple of (mime_type, image_bytes) of the first frame
        """
        try:
            # Download the video to a temporary file
            video_bytes = await attachment.read()
            with tempfile.NamedTemporaryFile(suffix=os.path.splitext(attachment.filename)[1], delete=False) as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(video_bytes)

            try:
                # Open the video with OpenCV
                cap = cv2.VideoCapture(temp_file_path)
                ret, frame = cap.read()

                if not ret:
                    print(f"Failed to read frame from video: {attachment.filename}")
                    return None, None

                # Convert BGR to RGB (OpenCV uses BGR by default)
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Convert to PIL Image
                pil_image = Image.fromarray(frame_rgb)

                # Save to bytes buffer
                output = io.BytesIO()
                pil_image.save(output, format='JPEG')
                output.seek(0)

                # Clean up
                cap.release()

                return "image/jpeg", output.getvalue()
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    print(f"Error removing temporary file: {e}")
        except Exception as e:
            print(f"Error processing video: {e}")
            return None, None

    # --- AI Moderation Command Group ---
    aimod_group = app_commands.Group(name="aimod", description="AI Moderation commands.")
    config_subgroup = app_commands.Group(name="config", description="Configure AI moderation settings.", parent=aimod_group)
    infractions_subgroup = app_commands.Group(name="infractions", description="Manage user infractions.", parent=aimod_group)
    model_subgroup = app_commands.Group(name="model", description="Manage the AI model for moderation.", parent=aimod_group)
    debug_subgroup = app_commands.Group(name="debug", description="Debugging commands for AI moderation.", parent=aimod_group)

    @config_subgroup.command(name="log_channel", description="Set the moderation log channel.")
    @app_commands.describe(channel="The text channel to use for moderation logs.")
    @app_commands.checks.has_permissions(administrator=True)
    async def modset_log_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        set_guild_config(interaction.guild.id, "MOD_LOG_CHANNEL_ID", channel.id)
        await interaction.response.send_message(f"Moderation log channel set to {channel.mention}.", ephemeral=False)

    @config_subgroup.command(name="suggestions_channel", description="Set the suggestions channel.")
    @app_commands.describe(channel="The text channel to use for suggestions.")
    @app_commands.checks.has_permissions(administrator=True)
    async def modset_suggestions_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        set_guild_config(interaction.guild.id, "SUGGESTIONS_CHANNEL_ID", channel.id)
        await interaction.response.send_message(f"Suggestions channel set to {channel.mention}.", ephemeral=False)

    @config_subgroup.command(name="moderator_role", description="Set the moderator role.")
    @app_commands.describe(role="The role that identifies moderators.")
    @app_commands.checks.has_permissions(administrator=True)
    async def modset_moderator_role(self, interaction: discord.Interaction, role: discord.Role):
        set_guild_config(interaction.guild.id, "MODERATOR_ROLE_ID", role.id)
        await interaction.response.send_message(f"Moderator role set to {role.mention}.", ephemeral=False)

    @config_subgroup.command(name="suicidal_ping_role", description="Set the role to ping for suicidal content.")
    @app_commands.describe(role="The role to ping for urgent suicidal content alerts.")
    @app_commands.checks.has_permissions(administrator=True)
    async def modset_suicidal_ping_role(self, interaction: discord.Interaction, role: discord.Role):
        set_guild_config(interaction.guild.id, "SUICIDAL_PING_ROLE_ID", role.id)
        await interaction.response.send_message(f"Suicidal content ping role set to {role.mention}.", ephemeral=False)

    @config_subgroup.command(name="add_nsfw_channel", description="Add a channel to the list of NSFW channels.")
    @app_commands.describe(channel="The text channel to mark as NSFW for the bot.")
    @app_commands.checks.has_permissions(administrator=True)
    async def modset_add_nsfw_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild.id
        nsfw_channels: list[int] = get_guild_config(guild_id, "NSFW_CHANNEL_IDS", [])
        if channel.id not in nsfw_channels:
            nsfw_channels.append(channel.id)
            set_guild_config(guild_id, "NSFW_CHANNEL_IDS", nsfw_channels)
            await interaction.response.send_message(f"{channel.mention} added to NSFW channels list.", ephemeral=False)
        else:
            await interaction.response.send_message(f"{channel.mention} is already in the NSFW channels list.", ephemeral=True)

    @config_subgroup.command(name="remove_nsfw_channel", description="Remove a channel from the list of NSFW channels.")
    @app_commands.describe(channel="The text channel to remove from the NSFW list.")
    @app_commands.checks.has_permissions(administrator=True)
    async def modset_remove_nsfw_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = interaction.guild.id
        nsfw_channels: list[int] = get_guild_config(guild_id, "NSFW_CHANNEL_IDS", [])
        if channel.id in nsfw_channels:
            nsfw_channels.remove(channel.id)
            set_guild_config(guild_id, "NSFW_CHANNEL_IDS", nsfw_channels)
            await interaction.response.send_message(f"{channel.mention} removed from NSFW channels list.", ephemeral=False)
        else:
            await interaction.response.send_message(f"{channel.mention} is not in the NSFW channels list.", ephemeral=True)

    @config_subgroup.command(name="list_nsfw_channels", description="List currently configured NSFW channels.")
    @app_commands.checks.has_permissions(administrator=True)
    async def modset_list_nsfw_channels(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        nsfw_channel_ids: list[int] = get_guild_config(guild_id, "NSFW_CHANNEL_IDS", [])
        if not nsfw_channel_ids:
            await interaction.response.send_message("No NSFW channels are currently configured.", ephemeral=False)
            return

        channel_mentions = []
        for channel_id in nsfw_channel_ids:
            channel_obj = interaction.guild.get_channel(channel_id)
            if channel_obj:
                channel_mentions.append(channel_obj.mention)
            else:
                channel_mentions.append(f"ID:{channel_id} (not found)")

        await interaction.response.send_message(f"Configured NSFW channels:\n- " + "\n- ".join(channel_mentions), ephemeral=False)

    # Note: The @app_commands.command(name="modenable", ...) and other commands like
    # viewinfractions, clearinfractions, modsetmodel, modgetmodel remain as top-level commands
    # as they were not part of the original "modset" generic command structure.
    # If these also need to be grouped, that would be a separate consideration.

    @config_subgroup.command(name="enable", description="Enable or disable moderation for this guild (admin only).")
    @app_commands.describe(enabled="Enable moderation (true/false)")
    async def modenable(self, interaction: discord.Interaction, enabled: bool):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You must be an administrator to use this command.", ephemeral=False)
            return
        set_guild_config(interaction.guild.id, "ENABLED", enabled)
        await interaction.response.send_message(f"Moderation is now {'enabled' if enabled else 'disabled'} for this guild.", ephemeral=False)

    @infractions_subgroup.command(name="view", description="View a user's AI moderation infraction history (mod/admin only).")
    @app_commands.describe(user="The user to view infractions for")
    async def viewinfractions(self, interaction: discord.Interaction, user: discord.Member):
        # Check if user has permission (admin or moderator role)
        moderator_role_id = get_guild_config(interaction.guild.id, "MODERATOR_ROLE_ID")
        moderator_role = interaction.guild.get_role(moderator_role_id) if moderator_role_id else None

        has_permission = (interaction.user.guild_permissions.administrator or
                         (moderator_role and moderator_role in interaction.user.roles))

        if not has_permission:
            await interaction.response.send_message("You must be an administrator or have the moderator role to use this command.", ephemeral=True)
            return

        # Get the user's infraction history
        infractions = get_user_infraction_history(interaction.guild.id, user.id)

        if not infractions:
            await interaction.response.send_message(f"{user.mention} has no recorded infractions.", ephemeral=False)
            return

        # Create an embed to display the infractions
        embed = discord.Embed(
            title=f"Infraction History for {user.display_name}",
            description=f"User ID: {user.id}",
            color=discord.Color.orange()
        )

        # Add each infraction to the embed
        for i, infraction in enumerate(infractions, 1):
            timestamp = infraction.get('timestamp', 'Unknown date')[:19].replace('T', ' ')  # Format ISO timestamp
            rule = infraction.get('rule_violated', 'Unknown rule')
            action = infraction.get('action_taken', 'Unknown action')
            reason = infraction.get('reasoning', 'No reason provided')

            # Truncate reason if it's too long
            if len(reason) > 200:
                reason = reason[:197] + "..."

            embed.add_field(
                name=f"Infraction #{i} - {timestamp}",
                value=f"**Rule Violated:** {rule}\n**Action Taken:** {action}\n**Reason:** {reason}",
                inline=False
            )

        embed.set_footer(text=f"Total infractions: {len(infractions)}")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed, ephemeral=False)

    @infractions_subgroup.command(name="clear", description="Clear a user's AI moderation infraction history (admin only).")
    @app_commands.describe(user="The user to clear infractions for")
    async def clearinfractions(self, interaction: discord.Interaction, user: discord.Member):
        # Check if user has administrator permission
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You must be an administrator to use this command.", ephemeral=True)
            return

        # Get the user's infraction history
        key = f"{interaction.guild.id}_{user.id}"
        infractions = USER_INFRACTIONS.get(key, [])

        if not infractions:
            await interaction.response.send_message(f"{user.mention} has no recorded infractions to clear.", ephemeral=False)
            return

        # Clear the user's infractions
        USER_INFRACTIONS[key] = []
        save_user_infractions()

        await interaction.response.send_message(f"Cleared {len(infractions)} infraction(s) for {user.mention}.", ephemeral=False)

    @model_subgroup.command(name="set", description="Change the AI model used for moderation (admin only).")
    @app_commands.describe(model="The OpenRouter model to use (e.g., 'google/gemini-2.5-flash-preview', 'anthropic/claude-3-opus-20240229')")
    async def modsetmodel(self, interaction: discord.Interaction, model: str):
        # Check if user has administrator permission
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You must be an administrator to use this command.", ephemeral=True)
            return

        # Validate the model name (basic validation)
        if not model or len(model) < 5 or "/" not in model:
            await interaction.response.send_message("Invalid model format. Please provide a valid OpenRouter model ID (e.g., 'google/gemini-2.5-flash-preview').", ephemeral=False)
            return

        # Save the model to guild configuration
        guild_id = interaction.guild.id
        set_guild_config(guild_id, "AI_MODEL", model)

        # Update the global model for immediate effect
        global OPENROUTER_MODEL
        OPENROUTER_MODEL = model

        await interaction.response.send_message(f"AI moderation model updated to `{model}` for this guild.", ephemeral=False)

    @modsetmodel.autocomplete('model')
    async def modsetmodel_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        print(f"[DEBUG] modsetmodel_autocomplete triggered. Current input: '{current}'")
        if not self.openrouter_models:
            print("[DEBUG] modsetmodel_autocomplete: openrouter_models list is empty or not loaded.")
            return [app_commands.Choice(name="⚠️ Models not loaded", value="")]

        print(f"[DEBUG] modsetmodel_autocomplete: Filtering {len(self.openrouter_models)} models with current: '{current}'")
        filtered_models = [
            m for m in self.openrouter_models
            if current.lower() in m["name"].lower() or current.lower() in m["id"].lower()
        ][:25]

        choices_to_return = [
            app_commands.Choice(name=m["name"][:100], value=m["id"][:100]) # Truncate name/value
            for m in filtered_models
        ]
        print(f"[DEBUG] modsetmodel_autocomplete returning {len(choices_to_return)} choices: {choices_to_return[:5]}")
        return choices_to_return

    @model_subgroup.command(name="get", description="View the current AI model used for moderation.")
    async def modgetmodel(self, interaction: discord.Interaction):
        # Get the model from guild config, fall back to global default
        guild_id = interaction.guild.id
        model_used = get_guild_config(guild_id, "AI_MODEL", OPENROUTER_MODEL)

        # Create an embed to display the model information
        embed = discord.Embed(
            title="AI Moderation Model",
            description=f"The current AI model used for moderation in this server is:",
            color=discord.Color.blue()
        )
        embed.add_field(name="Model", value=f"`{model_used}`", inline=False)
        embed.add_field(name="Default Model", value=f"`{OPENROUTER_MODEL}`", inline=False)
        embed.set_footer(text="Use /modsetmodel to change the model")

        await interaction.response.send_message(embed=embed, ephemeral=False)

    # Removed setup_hook as commands defined with @app_commands.command in a Cog
    # are typically automatically registered when the cog is added.
    # async def setup_hook(self):
    #     self.bot.tree.add_command(self.modset)
    #     self.bot.tree.add_command(self.modenable)
    #     self.bot.tree.add_command(self.viewinfractions)
    #     self.bot.tree.add_command(self.clearinfractions)
    #     self.bot.tree.add_command(self.modsetmodel)
    #     self.bot.tree.add_command(self.modgetmodel)

    async def query_openrouter(self, message: discord.Message, message_content: str, user_history: str, image_data_list=None):
        """
        Sends the message content, user history, and additional context to the OpenRouter API for analysis.
        Optionally includes image data for visual content moderation.

        Args:
            message: The original discord.Message object.
            message_content: The text content of the message.
            user_history: A string summarizing the user's past infractions.
            image_data_list: Optional list of tuples (mime_type, image_bytes, attachment_type, filename) for image moderation.

        Returns:
            A dictionary containing the AI's decision, or None if an error occurs.
            Expected format:
            {
              "reasoning": str,
              "violation": bool,
              "rule_violated": str ("None", "1", "5A", etc.),
              "action": str ("IGNORE", "WARN", "DELETE", "BAN", "NOTIFY_MODS")
            }
        """
        print(f"query_openrouter called. API key available: {self.openrouter_api_key is not None}")
        # Check if the API key was successfully fetched
        if not self.openrouter_api_key:
            print("Error: OpenRouter API Key is not available. Cannot query API.")
            return None

        # Construct the prompt for the AI model
        system_prompt_text = f"""You are an AI moderation assistant for a Discord server.
Your primary function is to analyze message content and attached media based STRICTLY on the server rules provided below, using all available context.

Server Rules:
---
{SERVER_RULES}
---

Context Provided:
You will receive the following information to aid your analysis:
- User's Server Role: (e.g., "Server Owner", "Admin", "Moderator", "Member").
- Channel Category: The name of the category the channel belongs to.
- Channel Age-Restricted/NSFW (Discord Setting): Boolean (true/false).
- Replied-to Message: If the current message is a reply, the content of the original message will be provided. This is crucial for understanding direct interactions.
- Recent Channel History: The last few messages in the channel to understand the flow of conversation.
- Attached Media: If the message contains image, GIF, or video attachments, they will be provided as image_url objects in the content array. For GIFs and videos, only the first frame is extracted.

Instructions:
1. Review the "Message Content" and any attached media against EACH rule, considering ALL provided context (User Role, Channel Info, Replied-to Message, Recent Channel History).
   - The "Channel Age-Restricted/NSFW (Discord Setting)" is the definitive indicator for NSFW content by Discord.
   - The "Channel Category" provides general context.
   - **"Replied-to Message" and "Recent Channel History" are vital for understanding banter, jokes, and ongoing discussions. A statement that seems offensive in isolation might be acceptable within the flow of conversation or as a direct reply.**
   - If images, GIFs, or videos are attached, analyze ALL of them for rule violations. For GIFs and videos, only the first frame is provided.
   - Pay special attention to images that may contain NSFW content, pornography, gore, or other prohibited visual content.
   - If multiple attachments are present, a violation in ANY of them should be flagged.
2. Determine if ANY rule is violated. When evaluating, consider the server's culture where **extremely edgy, dark, and sexual humor, including potentially offensive jokes (e.g., rape jokes, saying you want to be raped), are common and generally permissible IF THEY ARE CLEARLY JOKES, part of an established banter, or a direct non-malicious reply, and not targeted harassment or explicit rule violations.**
* **NSFW Content:**
The only rule regarding NSFW content is that **real-life pornography is strictly prohibited**.
Full-on pornographic images are permitted in designated NSFW channels.
Stickers and emojis are NOT considered "full-on pornographic images" and are allowed in any channel.
   - For general disrespectful behavior, harassment, or bullying (Rule 2 & 3): Only flag a violation if the intent appears **genuinely malicious, targeted, or serious, even after considering conversational history and replies.** Lighthearted insults or "wild" statements within an ongoing banter are generally permissible.
   - For **explicit slurs or severe discriminatory language** (Rule 3): These are violations **regardless of joking intent if they are used in a targeted or hateful manner**. Context from replies and history is still important to assess targeting.
   - CRITICAL: You should NOT consider the word "retard" or "retarded" as a slur in this server, as it is commonly used in a non-offensive context.
After considering the above, pay EXTREME attention to rules 5 (Pedophilia) and 5A (IRL Porn) – these are always severe. Rule 4 (AI Porn) is also critical. Prioritize these severe violations.
3. Respond ONLY with a single JSON object containing the following keys:
    - "reasoning": string (A concise explanation for your decision, referencing the specific rule and content).
    - "violation": boolean (true if any rule is violated, false otherwise)
    - "rule_violated": string (The number of the rule violated, e.g., "1", "5A", "None". If multiple rules are violated, state the MOST SEVERE one, prioritizing 5A > 5 > 4 > 3 > 2 > 1).
    - "action": string (Suggest ONE action from: "IGNORE", "WARN", "DELETE", "TIMEOUT_SHORT", "TIMEOUT_MEDIUM", "TIMEOUT_LONG", "KICK", "BAN", "NOTIFY_MODS", "SUICIDAL".
       Consider the user's infraction history. If the user has prior infractions for similar or escalating behavior, suggest a more severe action than if it were a first-time offense for a minor rule.
       Progressive Discipline Guide (unless overridden by severity):
         - First minor offense: "WARN" (and "DELETE" if content is removable like Rule 1/4).
         - Second minor offense / First moderate offense: "TIMEOUT_SHORT" (e.g., 10 minutes).
         - Repeated moderate offenses: "TIMEOUT_MEDIUM" (e.g., 1 hour).
         - Multiple/severe offenses: "TIMEOUT_LONG" (e.g., 1 day), "KICK", or "BAN".
       Spamming:
         - If a user continuously sends very long messages that are off-topic, repetitive, or appear to be meaningless spam (e.g., character floods, nonsensical text), suggest "TIMEOUT_MEDIUM" or "TIMEOUT_LONG" depending on severity and history, even if the content itself doesn't violate other specific rules. This is to maintain chat readability.
       Rule Severity Guidelines (use your judgment):
         - Consider the severity of each rule violation on its own merits.
         - Consider the user's history of past infractions when determining appropriate action.
         - Consider the context of the message and channel when evaluating violations.
         - You have full discretion to determine the most appropriate action for any violation.
       Suicidal Content:
         If the message content expresses **clear, direct, and serious suicidal ideation, intent, planning, or recent attempts** (e.g., 'I am going to end my life and have a plan', 'I survived my attempt last night', 'I wish I hadn't woken up after trying'), ALWAYS use "SUICIDAL" as the action, and set "violation" to true, with "rule_violated" as "Suicidal Content".
         For casual, edgy, hyperbolic, or ambiguous statements like 'imma kms', 'just kill me now', 'I want to die (lol)', or phrases that are clearly part of edgy humor/banter rather than a genuine cry for help, you should lean towards "IGNORE" or "NOTIFY_MODS" if there's slight ambiguity but no clear serious intent. **Do NOT flag 'imma kms' as "SUICIDAL" unless there is very strong supporting context indicating genuine, immediate, and serious intent.**
       If unsure but suspicious, or if the situation is complex: "NOTIFY_MODS".
       Default action for minor first-time rule violations should be "WARN" or "DELETE" (if applicable).
       Do not suggest "KICK" or "BAN" lightly; reserve for severe or repeated major offenses.
       Timeout durations: TIMEOUT_SHORT (approx 10 mins), TIMEOUT_MEDIUM (approx 1 hour), TIMEOUT_LONG (approx 1 day to 1 week).
       The system will handle the exact timeout duration; you just suggest the category.)

Example Response (Violation):
{{
  "reasoning": "The message content clearly depicts IRL non-consensual sexual content involving minors, violating rule 5A.",
  "violation": true,
  "rule_violated": "5A",
  "action": "BAN"
}}

Example Response (No Violation):
{{
  "reasoning": "The message is a respectful discussion and contains no prohibited content.",
  "violation": false,
  "rule_violated": "None",
  "action": "IGNORE"
}}

Example Response (Suicidal Content):
{{
  "reasoning": "The user's message 'I want to end my life' indicates clear suicidal intent.",
  "violation": true,
  "rule_violated": "Suicidal Content",
  "action": "SUICIDAL"
}}
"""

    system_prompt_text = f"""You are an AI moderation assistant for a Discord server.
Your primary function is to analyze message content and attached media based STRICTLY on the server rules provided below, using all available context.

Server Rules:
---
{SERVER_RULES}
---

Context Provided:
You will receive the following information to aid your analysis:
- User's Server Role: (e.g., "Server Owner", "Admin", "Moderator", "Member").
- Channel Category: The name of the category the channel belongs to.
- Channel Age-Restricted/NSFW (Discord Setting): Boolean (true/false).
- Replied-to Message: If the current message is a reply, the content of the original message will be provided. This is crucial for understanding direct interactions.
- Recent Channel History: The last few messages in the channel to understand the flow of conversation.

Instructions:
1. Review the "Message Content" against EACH rule, considering ALL provided context (User Role, Channel Info, Replied-to Message, Recent Channel History).
   - The "Channel Age-Restricted/NSFW (Discord Setting)" is the definitive indicator for NSFW content by Discord.
   - The "Channel Category" provides general context.
   - **"Replied-to Message" and "Recent Channel History" are vital for understanding banter, jokes, and ongoing discussions. A statement that seems offensive in isolation might be acceptable within the flow of conversation or as a direct reply.**
2. Determine if ANY rule is violated. When evaluating, consider the server's culture where **extremely edgy, dark, and sexual humor, including potentially offensive jokes (e.g., rape jokes, saying you want to be raped), are common and generally permissible IF THEY ARE CLEARLY JOKES, part of an established banter, or a direct non-malicious reply, and not targeted harassment or explicit rule violations.**
   - For Rule 1 (NSFW content):
     The only rules regarding NSFW content is that **real-life pornography is strictly prohibited**, and Full-on pornographic images are only permitted in designated NSFW channels.
     Stickers and emojis are NOT considered "full-on pornographic images" and are allowed in any channel.
   - For general disrespectful behavior, harassment, or bullying (Rule 2 & 3): Only flag a violation if the intent appears **genuinely malicious, targeted, or serious, even after considering conversational history and replies.** Lighthearted insults or "wild" statements within an ongoing banter are generally permissible.
   - For **explicit slurs or severe discriminatory language** (Rule 3): These are violations **regardless of joking intent if they are used in a targeted or hateful manner**. Context from replies and history is still important to assess targeting.
   - CRITICAL: You should NOT consider the word "retard" or "retarded" as a slur in this server, as it is commonly used in a non-offensive context.
After considering the above, pay EXTREME attention to rules 5 (Pedophilia) and 5A (IRL Porn) – these are always severe. Rule 4 (AI Porn) is also critical. Prioritize these severe violations.
3. Respond ONLY with a single JSON object containing the following keys:
    - "reasoning": string (A concise explanation for your decision, referencing the specific rule and content).
    - "violation": boolean (true if any rule is violated, false otherwise)
    - "rule_violated": string (The number of the rule violated, e.g., "1", "5A", "None". If multiple rules are violated, state the MOST SEVERE one, prioritizing 5A > 5 > 4 > 3 > 2 > 1).
    - "action": string (Suggest ONE action from: "IGNORE", "WARN", "DELETE", "TIMEOUT_SHORT", "TIMEOUT_MEDIUM", "TIMEOUT_LONG", "KICK", "BAN", "NOTIFY_MODS", "SUICIDAL".
       Consider the user's infraction history. If the user has prior infractions for similar or escalating behavior, suggest a more severe action than if it were a first-time offense for a minor rule.
       Progressive Discipline Guide (unless overridden by severity):
         - First minor offense: "WARN" (and "DELETE" if content is removable like Rule 1/4).
         - Second minor offense / First moderate offense: "TIMEOUT_SHORT" (e.g., 10 minutes).
         - Repeated moderate offenses: "TIMEOUT_MEDIUM" (e.g., 1 hour).
         - Multiple/severe offenses: "TIMEOUT_LONG" (e.g., 1 day), "KICK", or "BAN".
       Spamming:
         - If a user continuously sends very long messages that are off-topic, repetitive, or appear to be meaningless spam (e.g., character floods, nonsensical text), suggest "TIMEOUT_MEDIUM" or "TIMEOUT_LONG" depending on severity and history, even if the content itself doesn't violate other specific rules. This is to maintain chat readability.
       Rule Severity Guidelines (use your judgment):
         - Consider the severity of each rule violation on its own merits.
         - Consider the user's history of past infractions when determining appropriate action.
         - Consider the context of the message and channel when evaluating violations.
         - You have full discretion to determine the most appropriate action for any violation.
       Suicidal Content:
         If the message content expresses **clear, direct, and serious suicidal ideation, intent, planning, or recent attempts** (e.g., 'I am going to end my life and have a plan', 'I survived my attempt last night', 'I wish I hadn't woken up after trying'), ALWAYS use "SUICIDAL" as the action, and set "violation" to true, with "rule_violated" as "Suicidal Content".
         For casual, edgy, hyperbolic, or ambiguous statements like 'imma kms', 'just kill me now', 'I want to die (lol)', or phrases that are clearly part of edgy humor/banter rather than a genuine cry for help, you should lean towards "IGNORE" or "NOTIFY_MODS" if there's slight ambiguity but no clear serious intent. **Do NOT flag 'imma kms' as "SUICIDAL" unless there is very strong supporting context indicating genuine, immediate, and serious intent.**
       If unsure but suspicious, or if the situation is complex: "NOTIFY_MODS".
       Default action for minor first-time rule violations should be "WARN" or "DELETE" (if applicable).
       Do not suggest "KICK" or "BAN" lightly; reserve for severe or repeated major offenses.
       Timeout durations: TIMEOUT_SHORT (approx 10 mins), TIMEOUT_MEDIUM (approx 1 hour), TIMEOUT_LONG (approx 1 day to 1 week).
       The system will handle the exact timeout duration; you just suggest the category.)

Example Response (Violation):
{{
  "reasoning": "The message content clearly depicts IRL non-consensual sexual content involving minors, violating rule 5A.",
  "violation": true,
  "rule_violated": "5A",
  "action": "BAN"
}}

Example Response (No Violation):
{{
  "reasoning": "The message is a respectful discussion and contains no prohibited content.",
  "violation": false,
  "rule_violated": "None",
  "action": "IGNORE"
}}

Example Response (Suicidal Content):
{{
  "reasoning": "The user's message 'I want to end my life' indicates clear suicidal intent.",
  "violation": true,
  "rule_violated": "Suicidal Content",
  "action": "SUICIDAL"
}}
"""

    async def query_openrouter(self, message: discord.Message, message_content: str, user_history: str, image_data_list=None):
        """
        Sends the message content, user history, and additional context to the OpenRouter API for analysis.
        Optionally includes image data for visual content moderation.

        Args:
            message: The original discord.Message object.
            message_content: The text content of the message.
            user_history: A string summarizing the user's past infractions.
            image_data_list: Optional list of tuples (mime_type, image_bytes, attachment_type, filename) for image moderation.

        Returns:
            A dictionary containing the AI's decision, or None if an error occurs.
            Expected format:
            {
              "reasoning": str,
              "violation": bool,
              "rule_violated": str ("None", "1", "5A", etc.),
              "action": str ("IGNORE", "WARN", "DELETE", "BAN", "NOTIFY_MODS")
            }
        """
        print(f"query_openrouter called. API key available: {self.openrouter_api_key is not None}")
        # Check if the API key was successfully fetched
        if not self.openrouter_api_key:
            print("Error: OpenRouter API Key is not available. Cannot query API.")
            return None

        # Construct the prompt for the AI model
        system_prompt_text = f"""You are an AI moderation assistant for a Discord server.
Your primary function is to analyze message content and attached media based STRICTLY on the server rules provided below, using all available context.

Server Rules:
---
{SERVER_RULES}
---

Context Provided:
You will receive the following information to aid your analysis:
- User's Server Role: (e.g., "Server Owner", "Admin", "Moderator", "Member").
- Channel Category: The name of the category the channel belongs to.
- Channel Age-Restricted/NSFW (Discord Setting): Boolean (true/false).
- Replied-to Message: If the current message is a reply, the content of the original message will be provided. This is crucial for understanding direct interactions.
- Recent Channel History: The last few messages in the channel to understand the flow of conversation.
- Attached Media: If the message contains image, GIF, or video attachments, they will be provided as image_url objects in the content array. For GIFs and videos, only the first frame is extracted.

Instructions:
1. Review the "Message Content" and any attached media against EACH rule, considering ALL provided context (User Role, Channel Info, Replied-to Message, Recent Channel History).
   - The "Channel Age-Restricted/NSFW (Discord Setting)" is the definitive indicator for NSFW content by Discord.
   - The "Channel Category" provides general context.
   - **"Replied-to Message" and "Recent Channel History" are vital for understanding banter, jokes, and ongoing discussions. A statement that seems offensive in isolation might be acceptable within the flow of conversation or as a direct reply.**
   - If images, GIFs, or videos are attached, analyze ALL of them for rule violations. For GIFs and videos, only the first frame is provided.
   - Pay special attention to images that may contain NSFW content, pornography, gore, or other prohibited visual content.
   - If multiple attachments are present, a violation in ANY of them should be flagged.
2. Determine if ANY rule is violated. When evaluating, consider the server's culture where **extremely edgy, dark, and sexual humor, including potentially offensive jokes (e.g., rape jokes, saying you want to be raped), are common and generally permissible IF THEY ARE CLEARLY JOKES, part of an established banter, or a direct non-malicious reply, and not targeted harassment or explicit rule violations.**
* **NSFW Content:**
The only rule regarding NSFW content is that **real-life pornography is strictly prohibited**.
Full-on pornographic images are permitted in designated NSFW channels.
Stickers and emojis are NOT considered "full-on pornographic images" and are allowed in any channel.
   - For general disrespectful behavior, harassment, or bullying (Rule 2 & 3): Only flag a violation if the intent appears **genuinely malicious, targeted, or serious, even after considering conversational history and replies.** Lighthearted insults or "wild" statements within an ongoing banter are generally permissible.
   - For **explicit slurs or severe discriminatory language** (Rule 3): These are violations **regardless of joking intent if they are used in a targeted or hateful manner**. Context from replies and history is still important to assess targeting.
   - CRITICAL: You should NOT consider the word "retard" or "retarded" as a slur in this server, as it is commonly used in a non-offensive context.
After considering the above, pay EXTREME attention to rules 5 (Pedophilia) and 5A (IRL Porn) – these are always severe. Rule 4 (AI Porn) is also critical. Prioritize these severe violations.
3. Respond ONLY with a single JSON object containing the following keys:
    - "reasoning": string (A concise explanation for your decision, referencing the specific rule and content).
    - "violation": boolean (true if any rule is violated, false otherwise)
    - "rule_violated": string (The number of the rule violated, e.g., "1", "5A", "None". If multiple rules are violated, state the MOST SEVERE one, prioritizing 5A > 5 > 4 > 3 > 2 > 1).
    - "action": string (Suggest ONE action from: "IGNORE", "WARN", "DELETE", "TIMEOUT_SHORT", "TIMEOUT_MEDIUM", "TIMEOUT_LONG", "KICK", "BAN", "NOTIFY_MODS", "SUICIDAL".
       Consider the user's infraction history. If the user has prior infractions for similar or escalating behavior, suggest a more severe action than if it were a first-time offense for a minor rule.
       Progressive Discipline Guide (unless overridden by severity):
         - First minor offense: "WARN" (and "DELETE" if content is removable like Rule 1/4).
         - Second minor offense / First moderate offense: "TIMEOUT_SHORT" (e.g., 10 minutes).
         - Repeated moderate offenses: "TIMEOUT_MEDIUM" (e.g., 1 hour).
         - Multiple/severe offenses: "TIMEOUT_LONG" (e.g., 1 day), "KICK", or "BAN".
       Spamming:
         - If a user continuously sends very long messages that are off-topic, repetitive, or appear to be meaningless spam (e.g., character floods, nonsensical text), suggest "TIMEOUT_MEDIUM" or "TIMEOUT_LONG" depending on severity and history, even if the content itself doesn't violate other specific rules. This is to maintain chat readability.
       Rule Severity Guidelines (use your judgment):
         - Consider the severity of each rule violation on its own merits.
         - Consider the user's history of past infractions when determining appropriate action.
         - Consider the context of the message and channel when evaluating violations.
         - You have full discretion to determine the most appropriate action for any violation.
       Suicidal Content:
         If the message content expresses **clear, direct, and serious suicidal ideation, intent, planning, or recent attempts** (e.g., 'I am going to end my life and have a plan', 'I survived my attempt last night', 'I wish I hadn't woken up after trying'), ALWAYS use "SUICIDAL" as the action, and set "violation" to true, with "rule_violated" as "Suicidal Content".
         For casual, edgy, hyperbolic, or ambiguous statements like 'imma kms', 'just kill me now', 'I want to die (lol)', or phrases that are clearly part of edgy humor/banter rather than a genuine cry for help, you should lean towards "IGNORE" or "NOTIFY_MODS" if there's slight ambiguity but no clear serious intent. **Do NOT flag 'imma kms' as "SUICIDAL" unless there is very strong supporting context indicating genuine, immediate, and serious intent.**
       If unsure but suspicious, or if the situation is complex: "NOTIFY_MODS".
       Default action for minor first-time rule violations should be "WARN" or "DELETE" (if applicable).
       Do not suggest "KICK" or "BAN" lightly; reserve for severe or repeated major offenses.
       Timeout durations: TIMEOUT_SHORT (approx 10 mins), TIMEOUT_MEDIUM (approx 1 hour), TIMEOUT_LONG (approx 1 day to 1 week).
       The system will handle the exact timeout duration; you just suggest the category.)

Example Response (Violation):
{{
  "reasoning": "The message content clearly depicts IRL non-consensual sexual content involving minors, violating rule 5A.",
  "violation": true,
  "rule_violated": "5A",
  "action": "BAN"
}}

Example Response (No Violation):
{{
  "reasoning": "The message is a respectful discussion and contains no prohibited content.",
  "violation": false,
  "rule_violated": "None",
  "action": "IGNORE"
}}

Example Response (Suicidal Content):
{{
  "reasoning": "The user's message 'I want to end my life' indicates clear suicidal intent.",
  "violation": true,
  "rule_violated": "Suicidal Content",
  "action": "SUICIDAL"
}}
"""

    async def handle_violation(self, message: discord.Message, ai_decision: dict, notify_mods_message: str = None):
        """
        Takes action based on the AI's violation decision.
        Also transmits action info via HTTP POST with API key header.
        """
        import datetime
        import aiohttp

        rule_violated = ai_decision.get("rule_violated", "Unknown")
        reasoning = ai_decision.get("reasoning", "No reasoning provided.")
        action = ai_decision.get("action", "NOTIFY_MODS").upper() # Default to notify mods
        guild_id = message.guild.id # Get guild_id once
        user_id = message.author.id # Get user_id once

        moderator_role_id = get_guild_config(guild_id, "MODERATOR_ROLE_ID")
        moderator_role = message.guild.get_role(moderator_role_id) if moderator_role_id else None
        mod_ping = moderator_role.mention if moderator_role else f"Moderators (Role ID {moderator_role_id} not found)"

        current_timestamp_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # Get the model from guild config, fall back to global default (moved up from line 609)
        model_used = get_guild_config(guild_id, "AI_MODEL", OPENROUTER_MODEL)

        # --- Transmit action info over HTTP POST ---
        try:
            mod_log_api_secret = os.getenv("MOD_LOG_API_SECRET")
            if mod_log_api_secret:
                post_url = f"https://slipstreamm.dev/dashboard/api/guilds/{guild_id}/ai-moderation-action" #will be replaceing later with the Learnhelp API
                payload = {
                    "timestamp": current_timestamp_iso,
                    "guild_id": guild_id,
                    "guild_name": message.guild.name,
                    "channel_id": message.channel.id,
                    "channel_name": message.channel.name,
                    "message_id": message.id,
                    "message_link": message.jump_url,
                    "user_id": user_id,
                    "user_name": str(message.author),
                    "action": action, # This will be the AI suggested action before potential overrides
                    "rule_violated": rule_violated,
                    "reasoning": reasoning,
                    "violation": ai_decision.get("violation", False),
                    "message_content": message.content[:1024] if message.content else "",
                    "full_message_content": message.content if message.content else "",
                    "ai_model": model_used,
                    "result": "pending_system_action" # Indicates AI decision received, system action pending
                }
                headers = {
                    "Authorization": f"Bearer {mod_log_api_secret}",
                    "Content-Type": "application/json"
                }
                async with aiohttp.ClientSession() as http_session: # Renamed session to avoid conflict
                    async with http_session.post(post_url, headers=headers, json=payload, timeout=10) as resp:
                        # This payload is just for the initial AI decision log
                        # The actual outcome will be logged after the action is performed
                        if resp.status >= 400:
                             print(f"Failed to POST initial AI decision log: {resp.status}")
            else:
                print("MOD_LOG_API_SECRET not set; skipping initial action POST.")
        except Exception as e:
            print(f"Failed to POST initial action info: {e}")

        # --- Prepare Notification ---
        notification_embed = discord.Embed(
            title="🚨 Rule Violation Detected 🚨",
            description=f"AI analysis detected a violation of server rules.",
            color=discord.Color.red()
        )
        notification_embed.add_field(name="User", value=f"{message.author.mention} (`{message.author.id}`)", inline=False)
        notification_embed.add_field(name="Channel", value=message.channel.mention, inline=False)
        notification_embed.add_field(name="Rule Violated", value=f"**Rule {rule_violated}**", inline=True)
        notification_embed.add_field(name="AI Suggested Action", value=f"`{action}`", inline=True)
        notification_embed.add_field(name="AI Reasoning", value=f"_{reasoning}_", inline=False)
        notification_embed.add_field(name="Message Link", value=f"[Jump to Message]({message.jump_url})", inline=False)
        # Log message content and attachments for audit purposes
        msg_content = message.content if message.content else "*No text content*"
        notification_embed.add_field(name="Message Content", value=msg_content[:1024], inline=False)

        # Add attachment information if present
        if message.attachments:
            attachment_info = []
            for i, attachment in enumerate(message.attachments):
                attachment_info.append(f"{i+1}. {attachment.filename} ({attachment.content_type}) - [Link]({attachment.url})")
            attachment_text = "\n".join(attachment_info)
            notification_embed.add_field(name="Attachments", value=attachment_text[:1024], inline=False)

            # Add the first image as a thumbnail if it's an image type
            for attachment in message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in
                       self.image_extensions + self.gif_extensions + self.video_extensions):
                    notification_embed.set_thumbnail(url=attachment.url)
                    break
        # Use the model_used variable that was defined earlier
        notification_embed.set_footer(text=f"AI Model: {model_used}. Learnhelp AI Moderation.")
        notification_embed.timestamp = discord.utils.utcnow() # Use discord.utils.utcnow()

        action_taken_message = "" # To append to the notification

        # --- Perform Actions ---
        try:
            if action == "BAN":
                action_taken_message = f"Action Taken: User **BANNED** and message deleted."
                notification_embed.color = discord.Color.dark_red()
                try:
                    await message.delete()
                except discord.NotFound: print("Message already deleted before banning.")
                except discord.Forbidden:
                    print(f"WARNING: Missing permissions to delete message before banning user {message.author}.")
                    action_taken_message += " (Failed to delete message - check permissions)"
                ban_reason = f"AI Mod: Rule {rule_violated}. Reason: {reasoning}"
                await message.guild.ban(message.author, reason=ban_reason, delete_message_days=1)
                print(f"BANNED user {message.author} for violating rule {rule_violated}.")
                add_user_infraction(guild_id, user_id, rule_violated, "BAN", reasoning, current_timestamp_iso)

            elif action == "KICK":
                action_taken_message = f"Action Taken: User **KICKED** and message deleted."
                notification_embed.color = discord.Color.from_rgb(255, 127, 0) # Dark Orange
                try:
                    await message.delete()
                except discord.NotFound: print("Message already deleted before kicking.")
                except discord.Forbidden:
                    print(f"WARNING: Missing permissions to delete message before kicking user {message.author}.")
                    action_taken_message += " (Failed to delete message - check permissions)"
                kick_reason = f"AI Mod: Rule {rule_violated}. Reason: {reasoning}"
                await message.author.kick(reason=kick_reason)
                print(f"KICKED user {message.author} for violating rule {rule_violated}.")
                add_user_infraction(guild_id, user_id, rule_violated, "KICK", reasoning, current_timestamp_iso)

            elif action.startswith("TIMEOUT"):
                duration_seconds = 0
                duration_readable = ""
                if action == "TIMEOUT_SHORT":
                    duration_seconds = 10 * 60  # 10 minutes
                    duration_readable = "10 minutes"
                elif action == "TIMEOUT_MEDIUM":
                    duration_seconds = 60 * 60  # 1 hour
                    duration_readable = "1 hour"
                elif action == "TIMEOUT_LONG":
                    duration_seconds = 24 * 60 * 60 # 1 day
                    duration_readable = "1 day"

                if duration_seconds > 0:
                    action_taken_message = f"Action Taken: User **TIMED OUT for {duration_readable}** and message deleted."
                    notification_embed.color = discord.Color.blue()
                    try:
                        await message.delete()
                    except discord.NotFound: print(f"Message already deleted before timeout for {message.author}.")
                    except discord.Forbidden:
                        print(f"WARNING: Missing permissions to delete message before timeout for {message.author}.")
                        action_taken_message += " (Failed to delete message - check permissions)"

                    timeout_reason = f"AI Mod: Rule {rule_violated}. Reason: {reasoning}"
                    # discord.py timeout takes a timedelta object
                    await message.author.timeout(discord.utils.utcnow() + datetime.timedelta(seconds=duration_seconds), reason=timeout_reason)
                    print(f"TIMED OUT user {message.author} for {duration_readable} for violating rule {rule_violated}.")
                    add_user_infraction(guild_id, user_id, rule_violated, action, reasoning, current_timestamp_iso)
                else:
                    action_taken_message = "Action Taken: **Unknown timeout duration, notifying mods.**"
                    action = "NOTIFY_MODS" # Fallback if timeout duration is not recognized
                    print(f"Unknown timeout duration for action {action}. Defaulting to NOTIFY_MODS.")


            elif action == "DELETE":
                action_taken_message = f"Action Taken: Message **DELETED**."
                await message.delete()
                print(f"DELETED message from {message.author} for violating rule {rule_violated}.")
                # Typically, a simple delete isn't a formal infraction unless it's part of a WARN.
                # If you want to log deletes as infractions, add:
                # add_user_infraction(guild_id, user_id, rule_violated, "DELETE", reasoning, current_timestamp_iso)


            elif action == "WARN":
                action_taken_message = f"Action Taken: Message **DELETED** (AI suggested WARN)."
                notification_embed.color = discord.Color.orange()
                await message.delete() # Warnings usually involve deleting the offending message
                print(f"DELETED message from {message.author} (AI suggested WARN for rule {rule_violated}).")
                try:
                    dm_channel = await message.author.create_dm()
                    await dm_channel.send(
                        f"Your recent message in **{message.guild.name}** was removed for violating Rule **{rule_violated}**. "
                        f"Reason: _{reasoning}_. Please review the server rules. This is a formal warning."
                    )
                    action_taken_message += " User notified via DM with warning."
                except discord.Forbidden:
                    print(f"Could not DM warning to {message.author} (DMs likely disabled).")
                    action_taken_message += " (Could not DM user for warning)."
                except Exception as e:
                    print(f"Error sending warning DM to {message.author}: {e}")
                    action_taken_message += " (Error sending warning DM)."
                add_user_infraction(guild_id, user_id, rule_violated, "WARN", reasoning, current_timestamp_iso)


            elif action == "NOTIFY_MODS":
                action_taken_message = "Action Taken: **Moderator review requested.**"
                notification_embed.color = discord.Color.gold()
                print(f"Notifying moderators about potential violation (Rule {rule_violated}) by {message.author}.")
                # NOTIFY_MODS itself isn't an infraction on the user, but a request for human review.
                # If mods take action, they would log it manually or via a mod command.
                if notify_mods_message:
                    notification_embed.add_field(name="Additional Mod Message", value=notify_mods_message, inline=False)

            elif action == "SUICIDAL":
                action_taken_message = "Action Taken: **User DMed resources, relevant role notified.**"
                # No infraction is typically logged for "SUICIDAL" as it's a support action.
                notification_embed.title = "🚨 Suicidal Content Detected 🚨"
                notification_embed.color = discord.Color.dark_purple() # A distinct color
                notification_embed.description = "AI analysis detected content indicating potential suicidal ideation."
                print(f"SUICIDAL content detected from {message.author}. DMing resources and notifying role.")
                # DM the user with help resources
                try:
                    dm_channel = await message.author.create_dm()
                    await dm_channel.send(SUICIDAL_HELP_RESOURCES)
                    action_taken_message += " User successfully DMed."
                except discord.Forbidden:
                    print(f"Could not DM suicidal help resources to {message.author} (DMs likely disabled).")
                    action_taken_message += " (Could not DM user - DMs disabled)."
                except Exception as e:
                    print(f"Error sending suicidal help resources DM to {message.author}: {e}")
                    action_taken_message += f" (Error DMing user: {e})."
                # The message itself is usually not deleted for suicidal content, to allow for intervention.
                # If deletion is desired, add: await message.delete() here.

            else: # Includes "IGNORE" or unexpected actions
                if ai_decision.get("violation"): # If violation is true but action is IGNORE
                     action_taken_message = "Action Taken: **None** (AI suggested IGNORE despite flagging violation - Review Recommended)."
                     notification_embed.color = discord.Color.light_grey()
                     print(f"AI flagged violation ({rule_violated}) but suggested IGNORE for message by {message.author}. Notifying mods for review.")
                else:
                    # This case shouldn't be reached if called correctly, but handle defensively
                    print(f"No action taken for message by {message.author} (AI Action: {action}, Violation: False)")
                    return # Don't notify if no violation and action is IGNORE

            # --- Send Notification to Moderators/Relevant Role ---
            log_channel_id = get_guild_config(message.guild.id, "MOD_LOG_CHANNEL_ID")
            log_channel = self.bot.get_channel(log_channel_id) if log_channel_id else None
            if not log_channel:
                print(f"ERROR: Moderation log channel (ID: {log_channel_id}) not found or not configured. Defaulting to message channel.")
                log_channel = message.channel
                if not log_channel:
                    print(f"ERROR: Could not find even the original message channel {message.channel.id} to send notification.")
                    return

            if action == "SUICIDAL":
                suicidal_role_id = get_guild_config(message.guild.id, "SUICIDAL_PING_ROLE_ID")
                suicidal_role = message.guild.get_role(suicidal_role_id) if suicidal_role_id else None
                ping_target = suicidal_role.mention if suicidal_role else f"Role ID {suicidal_role_id} (Suicidal Content)"
                if not suicidal_role:
                    print(f"ERROR: Suicidal ping role ID {suicidal_role_id} not found.")
                final_message = f"{ping_target}\n{action_taken_message}"
                await log_channel.send(content=final_message, embed=notification_embed)
            elif moderator_role: # For other violations
                final_message = f"{mod_ping}\n{action_taken_message}"
                await log_channel.send(content=final_message, embed=notification_embed)
            else: # Fallback if moderator role is also not found for non-suicidal actions
                print(f"ERROR: Moderator role ID {moderator_role_id} not found for action {action}.")


        except discord.Forbidden as e:
            print(f"ERROR: Missing Permissions to perform action '{action}' for rule {rule_violated}. Details: {e}")
            # Try to notify mods about the failure
            if moderator_role:
                try:
                    await message.channel.send(
                        f"{mod_ping} **PERMISSION ERROR!** Could not perform action `{action}` on message by {message.author.mention} "
                        f"for violating Rule {rule_violated}. Please check bot permissions.\n"
                        f"Reasoning: _{reasoning}_\nMessage Link: {message.jump_url}"
                    )
                except discord.Forbidden:
                    print("FATAL: Bot lacks permission to send messages, even error notifications.")
        except discord.NotFound:
             print(f"Message {message.id} was likely already deleted when trying to perform action '{action}'.")
        except Exception as e:
            print(f"An unexpected error occurred during action execution for message {message.id}: {e}")
            # Try to notify mods about the unexpected error
            if moderator_role:
                 try:
                    await message.channel.send(
                        f"{mod_ping} **UNEXPECTED ERROR!** An error occurred while handling rule violation "
                        f"for {message.author.mention}. Please check bot logs.\n"
                        f"Rule: {rule_violated}, Action Attempted: {action}\nMessage Link: {message.jump_url}"
                    )
                 except discord.Forbidden:
                    print("FATAL: Bot lacks permission to send messages, even error notifications.")


    @commands.Cog.listener(name="on_message")
    async def message_listener(self, message: discord.Message):
        """Listens to messages and triggers moderation checks."""
        print(f"on_message triggered for message ID: {message.id}")
        # --- Basic Checks ---
        # Ignore messages from bots (including self)
        if message.author.bot:
            print(f"Ignoring message {message.id} from bot.")
            return
        # Ignore messages without content or attachments
        if not message.content and not message.attachments:
             print(f"Ignoring message {message.id} with no content or attachments.")
             return
        # Ignore DMs
        if not message.guild:
            print(f"Ignoring message {message.id} from DM.")
            return
        # Check if moderation is enabled for this guild
        if not get_guild_config(message.guild.id, "ENABLED", True):
            print(f"Moderation disabled for guild {message.guild.id}. Ignoring message {message.id}.")
            return

        # --- Suicidal Content Check ---
        # Suicidal keyword check removed; handled by OpenRouter AI moderation.

        # --- Prepare for AI Analysis ---
        message_content = message.content

        # Check for attachments
        image_data_list = []
        if message.attachments:
            # Process all attachments
            for attachment in message.attachments:
                mime_type, image_bytes, attachment_type = await self.process_attachment(attachment)
                if mime_type and image_bytes and attachment_type:
                    image_data_list.append((mime_type, image_bytes, attachment_type, attachment.filename))
                    print(f"Processed attachment: {attachment.filename} as {attachment_type}")

            # Log the number of attachments processed
            if image_data_list:
                print(f"Processed {len(image_data_list)} attachments for message {message.id}")

        # Only proceed with AI analysis if there's text to analyze or attachments
        if not message_content and not image_data_list:
            print(f"Ignoring message {message.id} with no content or valid attachments.")
            return

        # NSFW channel check removed - AI will handle this context

        # --- Call AI for Analysis (All Rules) ---
        # Check if the API key was successfully fetched and is available
        if not self.openrouter_api_key:
             print(f"Skipping AI analysis for message {message.id}: OpenRouter API Key is not available.")
             return

        # Prepare user history for the AI
        infractions = get_user_infraction_history(message.guild.id, message.author.id)
        history_summary_parts = []
        if infractions:
            for infr in infractions:
                history_summary_parts.append(f"- Action: {infr.get('action_taken', 'N/A')} for Rule {infr.get('rule_violated', 'N/A')} on {infr.get('timestamp', 'N/A')[:10]}. Reason: {infr.get('reasoning', 'N/A')[:50]}...")
        user_history_summary = "\n".join(history_summary_parts) if history_summary_parts else "No prior infractions recorded."

        # Limit history summary length to prevent excessively long prompts
        max_history_len = 500
        if len(user_history_summary) > max_history_len:
            user_history_summary = user_history_summary[:max_history_len-3] + "..."


        print(f"Analyzing message {message.id} from {message.author} in #{message.channel.name} with history...")
        if image_data_list:
            attachment_types = [data[2] for data in image_data_list]
            print(f"Including {len(image_data_list)} attachments in analysis: {', '.join(attachment_types)}")
        ai_decision = await self.query_openrouter(message, message_content, user_history_summary, image_data_list)

        # --- Process AI Decision ---
        if not ai_decision:
            print(f"Failed to get valid AI decision for message {message.id}.")
            # Optionally notify mods about AI failure if it happens often
            # Store the failure attempt for debugging
            self.last_ai_decisions.append({
                "message_id": message.id,
                "author_name": str(message.author),
                "author_id": message.author.id,
                "message_content_snippet": message.content[:100] + "..." if len(message.content) > 100 else message.content,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "ai_decision": {"error": "Failed to get valid AI decision", "raw_response": None} # Simplified error logging
            })
            return # Stop if AI fails or returns invalid data

        # Store the AI decision regardless of violation status
        self.last_ai_decisions.append({
            "message_id": message.id,
            "author_name": str(message.author),
            "author_id": message.author.id,
            "message_content_snippet": message.content[:100] + "..." if len(message.content) > 100 else message.content,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "ai_decision": ai_decision
        })

        # Check if the AI flagged a violation
        if ai_decision.get("violation"):
            # Handle the violation based on AI decision without overrides
            # Pass notify_mods_message if the action is NOTIFY_MODS
            notify_mods_message = ai_decision.get("notify_mods_message") if ai_decision.get("action") == "NOTIFY_MODS" else None
            await self.handle_violation(message, ai_decision, notify_mods_message)
        else:
            # AI found no violation
            print(f"AI analysis complete for message {message.id}. No violation detected.")

    @debug_subgroup.command(name="last_decisions", description="View the last 5 AI moderation decisions (admin only).")
    @app_commands.checks.has_permissions(administrator=True)
    async def aidebug_last_decisions(self, interaction: discord.Interaction):
        if not self.last_ai_decisions:
            await interaction.response.send_message("No AI decisions have been recorded yet.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Last 5 AI Moderation Decisions",
            color=discord.Color.purple()
        )
        embed.timestamp = discord.utils.utcnow()

        for i, record in enumerate(reversed(list(self.last_ai_decisions))): # Show newest first
            decision_info = record.get("ai_decision", {})
            violation = decision_info.get("violation", "N/A")
            rule_violated = decision_info.get("rule_violated", "N/A")
            reasoning = decision_info.get("reasoning", "N/A")
            action = decision_info.get("action", "N/A")
            error_msg = decision_info.get("error")

            field_value = (
                f"**Author:** {record.get('author_name', 'N/A')} ({record.get('author_id', 'N/A')})\n"
                f"**Message ID:** {record.get('message_id', 'N/A')}\n"
                f"**Content Snippet:** ```{record.get('message_content_snippet', 'N/A')}```\n"
                f"**Timestamp:** {record.get('timestamp', 'N/A')[:19].replace('T', ' ')}\n"
            )
            if error_msg:
                field_value += f"**Status:** <font color='red'>Error during processing: {error_msg}</font>\n"
            else:
                field_value += (
                    f"**Violation:** {violation}\n"
                    f"**Rule Violated:** {rule_violated}\n"
                    f"**Action:** {action}\n"
                    f"**Reasoning:** ```{reasoning}```\n"
                )

            # Truncate field_value if it's too long for an embed field
            if len(field_value) > 1024:
                field_value = field_value[:1020] + "..."

            embed.add_field(
                name=f"Decision #{len(self.last_ai_decisions) - i}",
                value=field_value,
                inline=False
            )
            if len(embed.fields) >= 5: # Limit to 5 fields in one embed for very long entries, or send multiple embeds
                break

        if not embed.fields: # Should not happen if self.last_ai_decisions is not empty
             await interaction.response.send_message("Could not format AI decisions.", ephemeral=True)
             return

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @aidebug_last_decisions.error
    async def aidebug_last_decisions_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You must be an administrator to use this command.", ephemeral=True)
        else:
            await interaction.response.send_message(f"An error occurred: {error}", ephemeral=True)
            print(f"Error in aidebug_last_decisions command: {error}")


# Setup function required by discord.py to load the cog
async def setup(bot: commands.Bot):
    """Loads the ModerationCog."""
    await bot.add_cog(ModerationCog(bot))
    print("ModerationCog has been loaded.")
