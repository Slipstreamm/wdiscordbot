import discord
from discord import app_commands
from discord.ext import commands
from io import BytesIO
from PIL import Image
import json

class FileConvert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="fileconvert", description="Convert a file to another format and send it here or via DM.")
    @app_commands.describe(
        attachment="The file to convert",
        target_format="The format to convert to (e.g. png, jpg, ico, txt, md, json)",
        dm_result="Send the result via DM instead of in this channel"
    )
    async def fileconvert(
        self,
        interaction: discord.Interaction,
        attachment: discord.Attachment,
        target_format: str,
        dm_result: bool = False
    ):
        await interaction.response.defer(thinking=True)
        supported_formats = ["png", "jpg", "jpeg", "ico", "json", "txt", "md"]
        target_format = target_format.lower()
        if target_format not in supported_formats:
            await interaction.followup.send(f"Unsupported target format: `{target_format}`. Supported: {', '.join(supported_formats)}")
            return

        file_bytes = await attachment.read()
        filename = attachment.filename.rsplit('.', 1)[0]
        output = BytesIO()
        output_filename = f"{filename}.{target_format}"

        # Try image conversion
        if attachment.content_type and attachment.content_type.startswith("image"):
            try:
                with Image.open(BytesIO(file_bytes)) as img:
                    if target_format == "jpg":
                        target_format_pil = "JPEG"
                    elif target_format == "png":
                        target_format_pil = "PNG"
                    elif target_format == "ico":
                        target_format_pil = "ICO"
                    else:
                        target_format_pil = target_format.upper()
                    img.save(output, format=target_format_pil)
                    output.seek(0)
            except Exception as e:
                await interaction.followup.send(f"Image conversion failed: {e}")
                return
        # Try text-based conversion
        elif target_format in ["txt", "md", "json"]:
            try:
                text = file_bytes.decode("utf-8")
                if target_format == "json":
                    # Try to parse and pretty-print JSON
                    try:
                        obj = json.loads(text)
                        text = json.dumps(obj, indent=2)
                    except Exception:
                        pass  # Not valid JSON, just save as text
                output.write(text.encode("utf-8"))
                output.seek(0)
            except Exception as e:
                await interaction.followup.send(f"Text conversion failed: {e}")
                return
        else:
            await interaction.followup.send("Unsupported file type or conversion.")
            return

        file = discord.File(fp=output, filename=output_filename)
        if dm_result:
            try:
                await interaction.user.send("Here is your converted file:", file=file)
                await interaction.followup.send("File sent via DM!", ephemeral=True)
            except discord.Forbidden:
                await interaction.followup.send("Could not send DM. Do you have DMs disabled?", ephemeral=True)
        else:
            await interaction.followup.send("Here is your converted file:", file=file)

async def setup(bot):
    await bot.add_cog(FileConvert(bot))
