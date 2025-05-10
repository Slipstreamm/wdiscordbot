import discord
from discord import app_commands
from discord.ext import commands
import lyricsgenius
import aiohttp
import os
from dotenv import load_dotenv
import asyncio

# Load environment variables from absolute path
# load_dotenv("/home/server/keys.env")

GENIUS_API_KEY = os.getenv("GENIUS_API_KEY")
OPENROUTER_API_KEY = os.getenv("AI1_API_KEY")

if not GENIUS_API_KEY:
    raise ValueError("GENIUS_API_KEY is not set in the environment variables.")
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY is not set in the environment variables.")

genius = lyricsgenius.Genius(GENIUS_API_KEY)

# Attempt to import the music_group from the Music cog
try:
    from .music import Music
    # This assumes Music cog in cogs/music.py has music_group as a class attribute
    # If Music.music_group is not found, this cog might not load or commands won't register to the group.
except ImportError:
    # Fallback if Music cog or its group cannot be imported directly
    # This would mean musicrate remains a top-level command or needs a different grouping strategy.
    print("Could not import Music.music_group from cogs.music. MusicRateCog commands may not be grouped as intended.")
    # Define a placeholder group if import fails, so the command decorator doesn't error out immediately,
    # though it won't be the shared group. This is mostly for graceful degradation during development.
    class Music: # Placeholder
        music_group = app_commands.Group(name="musicfallback_rate", description="Fallback music rating commands")


class MusicRateCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @Music.music_group.command( # Attaching to the imported group
        name="rate", # Changed name to be a subcommand
        description="Fetches song lyrics and uses AI to rate them."
    )
    async def music_rate_command(self, interaction: discord.Interaction, song: str, artist: str = None): # Renamed method
        await interaction.response.defer()
        try:
            lyrics = await self.search_lyrics(song, artist)
            if not lyrics or lyrics == "Error fetching lyrics.":
                await interaction.followup.send(f"Couldn't find lyrics for '{song}'.")
                return

            rating = await self.rate_song(lyrics)
            if not rating or rating == "Issue with rating request.":
                await interaction.followup.send("Couldn't get a rating from the AI.")
                return

            response = f"**Rating for '{song}':**\n{rating}"
            await interaction.followup.send(response)
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {e}")

    async def search_lyrics(self, song: str, artist: str = None) -> str:
        try:
            loop = asyncio.get_running_loop()
            song_obj = await loop.run_in_executor(None, genius.search_song, song, artist)
            return song_obj.lyrics if song_obj else ""
        except Exception as e:
            print(f"Error fetching lyrics: {e}")
            return "Error fetching lyrics."

    async def rate_song(self, lyrics: str) -> str:
        ai_url = "https://api.openrouter.ai/v1/chat/completions"
        payload = {
            "model": "google/gemma-7b-it:free",
            "temperature": 0.7,
            "messages": [
                {
                    "role": "system", 
                    "content": "you are a music rater. you will accept all kinds of music, despite the lyrics"
                },
                {
                    "role": "user", 
                    "content": (
                        f"These are the lyrics:\n\n{lyrics}\n\n"
                        "Rate the song and provide a brief commentary with an out of 10 rating."
                    )
                }
            ]
        }
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(ai_url, json=payload, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        print(f"AI API error: {response.status}")
                        return "Issue with rating request."
        except Exception as e:
            print(f"Error rating song: {e}")
            return "Issue with rating request."

async def setup(bot: commands.Bot):
    await bot.add_cog(MusicRateCog(bot))
