import discord
from discord import app_commands
from discord.ext import commands
import random
from typing import Optional

# A sample shop inventory. Here the keys are item names (in lowercase)
# and the values are the cost. When selling, we assume you get about half the price.
SHOP_ITEMS = {
    "pen": 20,
    "notebook": 50,
    "backpack": 100,
    "headphones": 200,
    "Temu Iphone 69326": 75,
    "Temu Macbook water": 100,
    "phone": 150,
    "Dell Optiplex 3020 M": 200,
    "Asus Vivobook 14": 175,
    "Kasane Teto plushie": 50,
    "miku plushie": 50,
    "RARE Golden Teto Plusie": 20000,
}

class Fun(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # A simple in-memory economy store where each user starts with $100 and an empty inventory.
        self.economy = {}  # {user_id: {"balance": int, "inventory": list}}

    def get_account(self, user_id: int) -> dict:
        """Creates an account for the user if one does not exist and returns it."""
        if user_id not in self.economy:
            self.economy[user_id] = {"balance": 100, "inventory": []}
        return self.economy[user_id]

    # Create a slash command group called "fun"
    fun_group = app_commands.Group(name="fun", description="Fun economy commands")

    @fun_group.command(name="work", description="Work a job and earn money!")
    async def work(self, interaction: discord.Interaction):
        account = self.get_account(interaction.user.id)
        earned = random.randint(50, 150)
        job = random.choice(["barista", "cashier", "developer", "bartender", "freelancer"])
        account["balance"] += earned
        await interaction.response.send_message(
            f"You worked as a {job} and earned ${earned}.\nYour new balance is ${account['balance']}."
        )

    @fun_group.command(name="sell", description="Sell an item from your inventory.")
    @app_commands.describe(item="The item you wish to sell.")
    async def sell(self, interaction: discord.Interaction, item: str):
        account = self.get_account(interaction.user.id)
        # Find the item in your inventory (ignoring case)
        item_in_inventory = None
        for inv_item in account["inventory"]:
            if inv_item.lower() == item.lower():
                item_in_inventory = inv_item
                break

        if not item_in_inventory:
            await interaction.response.send_message("You don't have that item in your inventory!")
            return

        # Remove the item and determine its selling price.
        account["inventory"].remove(item_in_inventory)
        # Use the shop price if known, otherwise default to $20; you get roughly half when selling.
        sold_price = SHOP_ITEMS.get(item_in_inventory.lower(), 20) // 2
        account["balance"] += sold_price
        await interaction.response.send_message(
            f"You sold your {item_in_inventory} for ${sold_price}.\nYour new balance is ${account['balance']}."
        )

    @fun_group.command(name="steal", description="Attempt to steal money from another user!")
    @app_commands.describe(target="The member you want to steal from.")
    async def steal(self, interaction: discord.Interaction, target: discord.Member):
        # Prevent stealing from oneself
        if target.id == interaction.user.id:
            await interaction.response.send_message("You can't steal from yourself!")
            return

        thief = self.get_account(interaction.user.id)
        victim = self.get_account(target.id)
        if victim["balance"] < 50:
            await interaction.response.send_message(f"{target.display_name} doesn't have enough money to steal!")
            return

        # Simulate theft with a 30% chance of success.
        if random.random() < 0.3:
            # On success: steal a random amount between $10 and up to one-third of the victim's balance (max $100).
            stolen = random.randint(10, min(100, victim["balance"] // 3))
            victim["balance"] -= stolen
            thief["balance"] += stolen
            await interaction.response.send_message(
                f"You successfully stole ${stolen} from {target.display_name}!\nYour new balance is ${thief['balance']}."
            )
        else:
            # On failure, the thief is fined a small amount.
            fine = random.randint(5, 20)
            thief["balance"] = max(0, thief["balance"] - fine)
            await interaction.response.send_message(
                f"You got caught trying to steal from {target.display_name}!\nYou were fined ${fine}.\nYour new balance is ${thief['balance']}."
            )

    @fun_group.command(name="shop", description="View shop items or buy an item.")
    @app_commands.describe(item="The item you wish to buy (optional). Leave empty to view available items.")
    async def shop(self, interaction: discord.Interaction, item: Optional[str] = None):
        account = self.get_account(interaction.user.id)
        if item is None:
            # List all available shop items.
            items_list = "\n".join([f"{name.title()} - ${price}" for name, price in SHOP_ITEMS.items()])
            response = f"**Available Items:**\n{items_list}\n\nTo buy an item, use `/fun shop <item>`."
            await interaction.response.send_message(response)
        else:
            item_key = item.lower()
            if item_key not in SHOP_ITEMS:
                await interaction.response.send_message("That item is not available in the shop!")
                return
            price = SHOP_ITEMS[item_key]
            if account["balance"] < price:
                await interaction.response.send_message("You don't have enough money to buy that item!")
                return
            # Deduct the price and add the item to the user's inventory.
            account["balance"] -= price
            account["inventory"].append(item_key)
            await interaction.response.send_message(
                f"You bought a {item.title()} for ${price}.\nYour new balance is ${account['balance']}."
            )

    @fun_group.command(name="gamble", description="Gamble a certain amount of money in a coin flip!")
    @app_commands.describe(amount="The amount of money you want to gamble.")
    async def gamble(self, interaction: discord.Interaction, amount: int):
        if amount <= 0:
            await interaction.response.send_message("You must gamble a positive amount!")
            return

        account = self.get_account(interaction.user.id)
        if account["balance"] < amount:
            await interaction.response.send_message("You don't have that much money!")
            return

        # Simple coin flip: win doubles your bet, lose subtracts it.
        if random.choice([True, False]):
            account["balance"] += amount
            await interaction.response.send_message(
                f"You won! You earned an extra ${amount}.\nYour new balance is ${account['balance']}."
            )
        else:
            account["balance"] -= amount
            await interaction.response.send_message(
                f"You lost the gamble and lost ${amount}.\nYour new balance is ${account['balance']}."
            )

# The setup function to add this cog and register the command group.
async def setup(bot: commands.Bot):
    cog = Fun(bot)
    await bot.add_cog(cog)
    # Register the entire /fun group to the bot's command tree.
    bot.tree.add_command(Fun.fun_group)
