# cogs/fun.py
import discord
import random
from discord.ext import commands
from discord import app_commands
from enum import Enum

# Define an enum for coinflip
class CoinSide(str, Enum):
    heads = "heads"
    tails = "tails"

# --- View Classes (defined at module level) ---
class SchoolMenuView(discord.ui.View):
    def __init__(self): # Added __init__
        super().__init__(timeout=60) # Added timeout to init

    @discord.ui.button(label="Math", style=discord.ButtonStyle.primary, emoji="📚")
    async def math_button(self, interaction: discord.Interaction, _button: discord.ui.Button): # Added self
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Math Menu",
                description="- Calculator Smashing Contest\n- Pi Eating Challenge\n- Guess the Teacher's Age (Impossible)",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @discord.ui.button(label="Science", style=discord.ButtonStyle.primary, emoji="🔬")
    async def science_button(self, interaction: discord.Interaction, _button: discord.ui.Button): # Added self
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Science Menu",
                description="- Failed Lab Experiments\n- Mystery Substances Table\n- Who Set Off the Fire Alarm?",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @discord.ui.button(label="Literature", style=discord.ButtonStyle.primary, emoji="📖")
    async def literature_button(self, interaction: discord.Interaction, _button: discord.ui.Button): # Added self
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Literature Menu",
                description="- Last-Minute Essay Generator\n- Overanalyze That Poem\n- Shakespearean Roasts",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @discord.ui.button(label="Art", style=discord.ButtonStyle.primary, emoji="🎨")
    async def art_button(self, interaction: discord.Interaction, _button: discord.ui.Button): # Added self
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Art Menu",
                description="- Paint Water or Coffee?\n- Abstract Doodles Only\n- Glue Stick Speedrun",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @discord.ui.button(label="History", style=discord.ButtonStyle.primary, emoji="🏫")
    async def history_button(self, interaction: discord.Interaction, _button: discord.ui.Button): # Added self
        await interaction.response.send_message(
            embed=discord.Embed(
                title="History Menu",
                description="- Guess That Century\n- Ancient Meme Review\n- Who Actually Did Their Homework?",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

class PartyMenuView(discord.ui.View):
    def __init__(self): # Added __init__
        super().__init__(timeout=60) # Added timeout to init

    @discord.ui.button(label="Party Games", style=discord.ButtonStyle.primary, emoji="🎉")
    async def party_games(self, interaction: discord.Interaction, _button: discord.ui.Button): # Added self
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Party Games",
                description="- Charades\n- Musical Chairs\n- Dance Off",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @discord.ui.button(label="Music", style=discord.ButtonStyle.primary, emoji="🎶")
    async def music(self, interaction: discord.Interaction, _button: discord.ui.Button): # Added self
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Music",
                description="- Top 40 Playlist\n- Karaoke Time\n- DJ Requests",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @discord.ui.button(label="Food", style=discord.ButtonStyle.primary, emoji="🍕")
    async def food(self, interaction: discord.Interaction, _button: discord.ui.Button): # Added self
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Food",
                description="- Pizza\n- Chips & Dip\n- Cupcakes",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @discord.ui.button(label="Decorations", style=discord.ButtonStyle.primary, emoji="🎈")
    async def decorations(self, interaction: discord.Interaction, _button: discord.ui.Button): # Added self
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Decorations",
                description="- Balloons\n- Streamers\n- Confetti",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

class SnackMenuView(discord.ui.View):
    def __init__(self): # Added __init__
        super().__init__(timeout=60) # Added timeout to init

    @discord.ui.button(label="Burger", style=discord.ButtonStyle.primary, emoji="🍔")
    async def burger(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Burger",
                description="A delicious burger with all the fixings.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @discord.ui.button(label="Hot Dog", style=discord.ButtonStyle.primary, emoji="🌭")
    async def hotdog(self, interaction: discord.Interaction, _button: discord.ui.Button): 
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Hot Dog",
                description="A classic hot dog, perfect for any occasion.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @discord.ui.button(label="Soda", style=discord.ButtonStyle.primary, emoji="🥤")
    async def soda(self, interaction: discord.Interaction, _button: discord.ui.Button): 
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Soda",
                description="A refreshing soda to quench your thirst.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @discord.ui.button(label="Fries", style=discord.ButtonStyle.primary, emoji="🍟")
    async def fries(self, interaction: discord.Interaction, _button: discord.ui.Button): 
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Fries",
                description="Crispy golden fries, straight from the fryer.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @discord.ui.button(label="Pizza Slice", style=discord.ButtonStyle.primary, emoji="🍕")
    async def pizza(self, interaction: discord.Interaction, _button: discord.ui.Button): 
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Pizza Slice",
                description="A cheesy slice of pizza, just for you.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @discord.ui.button(label="Donut", style=discord.ButtonStyle.primary, emoji="🍩")
    async def donut(self, interaction: discord.Interaction, _button: discord.ui.Button): 
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Donut",
                description="A sweet donut to satisfy your cravings.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )
# --- End View Classes ---

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    menus_group = app_commands.Group(name="menus", description="Display various fun menus.")

    @menus_group.command(name="school", description="Displays a school menu.")
    async def school_menu_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Kasane's School Menu",
            description="Welcome to the school menu! Here's what we have on offer:",
            color=discord.Color.blue()
        )
        embed.add_field(name="📚 Math", value="Numbers, equations, and questionable life choices.", inline=False)
        embed.add_field(name="🔬 Science", value="Explosions, questionable experiments, and caffeine.", inline=False)
        embed.add_field(name="📖 Literature", value="Books, drama, and overdue essays.", inline=False)
        embed.add_field(name="🎨 Art", value="Paint, mess, and existential crises.", inline=False)
        embed.add_field(name="🏫 History", value="Dead people, wars, and dates you won't remember.", inline=False)
        embed.set_footer(text="Enjoy your learning! 📚")
        await interaction.response.send_message(embed=embed, view=SchoolMenuView())

    @menus_group.command(name="party", description="Displays a party menu.")
    async def party_menu_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Kasane's Party Menu",
            description="Welcome to the party menu! Here's what we have on offer:",
            color=discord.Color.blue()
        )
        embed.add_field(name="🎉 Party Games", value="Fun games to play with friends.", inline=False)
        embed.add_field(name="🎶 Music", value="Dance to the latest hits!", inline=False)
        embed.add_field(name="🍕 Food", value="Delicious snacks and drinks.", inline=False)
        embed.add_field(name="🎈 Decorations", value="Party decorations to set the mood.", inline=False)
        embed.set_footer(text="Let's get this party started! 🎊")
        await interaction.response.send_message(embed=embed, view=PartyMenuView())

    @menus_group.command(name="snack", description="Displays a snack menu.")
    async def snack_menu_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="Kasane's Snack Menu",
            description="Welcome to the snack menu! Here's what we have on offer:",
            color=discord.Color.blue()
        )
        embed.add_field(name="🍔 Burger", value="A delicious burger with all the fixings.", inline=False)
        embed.add_field(name="🌭 Hot Dog", value="A classic hot dog, perfect for any occasion.", inline=False)
        embed.add_field(name="🥤 Soda", value="A refreshing soda to quench your thirst.", inline=False)
        embed.add_field(name="🍟 Fries", value="Crispy golden fries, straight from the fryer.", inline=False)
        embed.add_field(name="🍕 Pizza Slice", value="A cheesy slice of pizza, just for you.", inline=False)
        embed.add_field(name="🍩 Donut", value="A sweet donut to satisfy your cravings.", inline=False)
        embed.set_footer(text="Enjoy your snacks! 🍴")
        await interaction.response.send_message(embed=embed, view=SnackMenuView())
        
async def setup(bot: commands.Bot):
    fun_cog = Fun(bot)
    await bot.add_cog(fun_cog)
