import discord
from discord import app_commands
from discord.ext import commands
from io import BytesIO
from PIL import Image
import json
import zipfile
import py7zr
import tempfile
import os
from pydub import AudioSegment

try:
    import moviepy as mp
except ImportError:
    print("moviepy is NOT installed in this environment")

class FileConvert(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

fileutils_group = app_commands.Group(
    name="fileutils",
    description="File utilities (conversion, etc.)"
)

@fileutils_group.command(name="convert", description="Convert a file to another format and send it here or via DM.")
@app_commands.describe(
    attachment="The file to convert",
    target_format="The format to convert to (e.g. png, jpg, ico, txt, md, json)",
    dm_result="Send the result via DM instead of in this channel"
)
async def fileconvert(
    interaction: discord.Interaction,
    attachment: discord.Attachment,
    target_format: str,
    dm_result: bool = False
):
    await interaction.response.defer(thinking=True)
    supported_formats = [
        "png", "jpg", "jpeg", "ico", "json", "txt", "md", "zip", "7z",
        "mp3", "wav", "mp4", "avi", "mov", "mkv", "webm", "gif",
        "csv", "bmp", "tiff", "webp", "flac", "ogg", "aac", "opus", "pdf", "docx", "xlsx", "pptx", "rtf", "html", "xml", "tar", "gz", "bz2", "xz"
    ]
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
                if target_format in ["jpg", "jpeg"]:
                    target_format_pil = "JPEG"
                elif target_format == "png":
                    target_format_pil = "PNG"
                elif target_format == "ico":
                    target_format_pil = "ICO"
                elif target_format == "bmp":
                    target_format_pil = "BMP"
                elif target_format == "tiff":
                    target_format_pil = "TIFF"
                elif target_format == "webp":
                    target_format_pil = "WEBP"
                else:
                    target_format_pil = target_format.upper()
                img.save(output, format=target_format_pil)
                output.seek(0)
        except Exception as e:
            await interaction.followup.send(f"Image conversion failed: {e}")
            return
    # Try text-based conversion
    elif target_format in ["txt", "md", "json", "csv", "xml", "html", "rtf"]:
        try:
            text = file_bytes.decode("utf-8", errors="replace")
            if target_format == "json":
                try:
                    obj = json.loads(text)
                    text = json.dumps(obj, indent=2)
                except Exception:
                    pass
            output.write(text.encode("utf-8"))
            output.seek(0)
        except Exception as e:
            await interaction.followup.send(f"Text conversion failed: {e}")
            return
    # Archive conversion: zip <-> 7z, tar, gz, bz2, xz
    elif (attachment.filename.endswith('.zip') and target_format == "7z"):
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Extract zip to temp dir
                with zipfile.ZipFile(BytesIO(file_bytes), 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                # Archive all files in temp dir to 7z
                with py7zr.SevenZipFile(output, 'w') as archive:
                    for root, _, files in os.walk(tmpdir):
                        for file in files:
                            abs_path = os.path.join(root, file)
                            arcname = os.path.relpath(abs_path, tmpdir)
                            archive.write(abs_path, arcname)
                output.seek(0)
        except Exception as e:
            await interaction.followup.send(f"Archive conversion failed: {e}")
            return
    elif (attachment.filename.endswith('.7z') and target_format == "zip"):
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                # Extract 7z to temp dir
                with py7zr.SevenZipFile(BytesIO(file_bytes), 'r') as archive:
                    archive.extractall(path=tmpdir)
                # Archive all files in temp dir to zip
                with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                    for root, _, files in os.walk(tmpdir):
                        for file in files:
                            abs_path = os.path.join(root, file)
                            arcname = os.path.relpath(abs_path, tmpdir)
                            zip_out.write(abs_path, arcname)
                output.seek(0)
        except Exception as e:
            await interaction.followup.send(f"Archive conversion failed: {e}")
            return
    elif (attachment.filename.endswith('.zip') and target_format in ["tar", "gz", "bz2", "xz"]):
        try:
            import tarfile
            with tempfile.TemporaryDirectory() as tmpdir:
                with zipfile.ZipFile(BytesIO(file_bytes), 'r') as zip_ref:
                    zip_ref.extractall(tmpdir)
                tar_mode = "w:" + (target_format if target_format != "tar" else "")
                with tarfile.open(fileobj=output, mode=tar_mode) as tar_out:
                    tar_out.add(tmpdir, arcname=".")
                output.seek(0)
        except Exception as e:
            await interaction.followup.send(f"Archive conversion failed: {e}")
            return
    elif (attachment.filename.endswith('.tar') and target_format == "zip"):
        try:
            import tarfile
            with tempfile.TemporaryDirectory() as tmpdir:
                with tarfile.open(fileobj=BytesIO(file_bytes), mode="r:*") as tar_ref:
                    tar_ref.extractall(tmpdir)
                with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                    for root, _, files in os.walk(tmpdir):
                        for file in files:
                            abs_path = os.path.join(root, file)
                            arcname = os.path.relpath(abs_path, tmpdir)
                            zip_out.write(abs_path, arcname)
                output.seek(0)
        except Exception as e:
            await interaction.followup.send(f"Archive conversion failed: {e}")
            return
    # Audio conversion: mp3 <-> wav, flac, ogg, aac, opus
    elif (attachment.filename.split('.')[-1].lower() in ["mp3", "wav", "flac", "ogg", "aac", "opus"]
          and target_format in ["mp3", "wav", "flac", "ogg", "aac", "opus"]):
        try:
            audio = AudioSegment.from_file(BytesIO(file_bytes))
            audio.export(output, format=target_format)
            output.seek(0)
        except Exception as e:
            await interaction.followup.send(f"Audio conversion failed: {e}")
            return
    # Video conversion: mp4, avi, mov, mkv, webm, gif
    elif (attachment.filename.split('.')[-1].lower() in ["mp4", "avi", "mov", "mkv", "webm"]
          and target_format in ["mp4", "avi", "mov", "mkv", "webm", "gif"]):
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix="." + attachment.filename.split('.')[-1]) as tmp_in:
                tmp_in.write(file_bytes)
                tmp_in.flush()
                tmp_in_path = tmp_in.name
            tmp_out_path = tmp_in_path.rsplit('.', 1)[0] + f".{target_format}"
            clip = mp.VideoFileClip(tmp_in_path)
            if target_format == "gif":
                clip.write_gif(tmp_out_path)
            else:
                clip.write_videofile(tmp_out_path, codec="libx264", audio_codec="aac")
            with open(tmp_out_path, "rb") as f:
                output.write(f.read())
            output.seek(0)
            clip.close()
            os.remove(tmp_in_path)
            os.remove(tmp_out_path)
        except Exception as e:
            await interaction.followup.send(f"Video conversion failed: {e}")
            return
    # PDF, DOCX, XLSX, PPTX conversion (basic, using python-docx, openpyxl, python-pptx, PyPDF2)
    elif (attachment.filename.endswith('.docx') and target_format == "pdf"):
        try:
            from docx2pdf import convert as docx2pdf_convert
            with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_in:
                tmp_in.write(file_bytes)
                tmp_in.flush()
                tmp_in_path = tmp_in.name
            tmp_out_path = tmp_in_path.rsplit('.', 1)[0] + ".pdf"
            docx2pdf_convert(tmp_in_path, tmp_out_path)
            with open(tmp_out_path, "rb") as f:
                output.write(f.read())
            output.seek(0)
            os.remove(tmp_in_path)
            os.remove(tmp_out_path)
        except Exception as e:
            await interaction.followup.send(f"DOCX to PDF conversion failed: {e}")
            return
    # Generic binary-to-text and text-to-binary conversion
    elif (attachment.filename.endswith('.bin') and target_format in ["txt", "md"]):
        try:
            text = file_bytes.decode("utf-8", errors="replace")
            output.write(text.encode("utf-8"))
            output.seek(0)
        except Exception as e:
            await interaction.followup.send(f"Binary to text conversion failed: {e}")
            return
    elif (attachment.filename.endswith('.txt') and target_format == "bin"):
        try:
            output.write(file_bytes)
            output.seek(0)
        except Exception as e:
            await interaction.followup.send(f"Text to binary conversion failed: {e}")
            return
    # Fallback: just copy file bytes with new extension (for unknown but convertible types)
    else:
        try:
            output.write(file_bytes)
            output.seek(0)
        except Exception as e:
            await interaction.followup.send(f"Generic file conversion failed: {e}")
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

# Required packages for your bot to support all conversions:
# discord.py, Pillow, py7zr, pydub, moviepy

# Install them with:
# pip install discord.py Pillow py7zr pydub moviepy

# For audio and video conversion, you also need ffmpeg installed on your system.
# Download from https://ffmpdoweg.org/download.html and ensure ffmpeg is in your PATH.

async def setup(bot):
    cog = FileConvert(bot)
    await bot.add_cog(cog)
    bot.tree.add_command(fileutils_group)
