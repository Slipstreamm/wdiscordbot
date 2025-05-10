import discord
from discord import app_commands
from discord.ext import commands
import random
from typing import Optional

# A sample shop inventory. The keys are item names (in lowercase) and the values are the cost.
# When selling, we assume you get about half the price.
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
    "RARE Golden Teto Plushie": 20000,
}

# A simple in-memory economy store where each user starts with $100 and an empty inventory.
economy = {}

def get_account(user_id: int) -> dict:
    """Creates an account for the user if one does not exist and returns it."""
    if user_id not in economy:
        economy[user_id] = {"balance": 100, "inventory": []}
    return economy[user_id]

# ------------------- User Commands -------------------

@app_commands.command(name="work", description="Work a job and earn money!")
async def work(interaction: discord.Interaction):
    account = get_account(interaction.user.id)
    earned = random.randint(50, 150)
    job = random.choice(["barista", "cashier", "developer", "bartender", "freelancer"])
    account["balance"] += earned

    embed = discord.Embed(
        title="Work",
        description=f"You worked as a **{job}** and earned **${earned}**.\nYour new balance is **${account['balance']}**.",
        color=discord.Color.blue()
    )
    await interaction.response.send_message(embed=embed)

@app_commands.command(name="sell", description="Sell an item from your inventory.")
@app_commands.describe(item="The item you wish to sell.")
async def sell(interaction: discord.Interaction, item: str):
    account = get_account(interaction.user.id)
    # Find the item in your inventory (ignoring case)
    item_in_inventory = None
    for inv_item in account["inventory"]:
        if inv_item.lower() == item.lower():
            item_in_inventory = inv_item
            break

    if not item_in_inventory:
        embed = discord.Embed(
            title="Sell",
            description="You don't have that item in your inventory!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    account["inventory"].remove(item_in_inventory)
    # Use the shop price if known, otherwise default to $20; you get roughly half when selling.
    sold_price = SHOP_ITEMS.get(item_in_inventory.lower(), 20) // 2
    account["balance"] += sold_price

    embed = discord.Embed(
        title="Sell",
        description=f"You sold your **{item_in_inventory}** for **${sold_price}**.\nYour new balance is **${account['balance']}**.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

@sell.autocomplete("item")
async def sell_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    account = get_account(interaction.user.id)
    # Use set to get unique items from inventory, as duplicates might exist
    # Items in inventory are stored with original casing from SHOP_ITEMS
    inventory_items = list(set(account.get("inventory", [])))
    # This part was missing from the diff, I'll add a placeholder for now
    # and ask the user to complete it.
    # TODO: Complete the autocomplete logic
    return [
        app_commands.Choice(name=item, value=item)
        for item in inventory_items if current.lower() in item.lower()
    ][:25]

@app_commands.command(name="steal", description="Attempt to steal money from another user!")
@app_commands.describe(target="The member you want to steal from.")
async def steal(interaction: discord.Interaction, target: discord.Member):
    account = get_account(interaction.user.id)
    thief = account
    victim = get_account(target.id)

    if target.id == interaction.user.id:
        embed = discord.Embed(
            title="Steal",
            description="You can't steal from yourself!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    if victim["balance"] < 50:
        embed = discord.Embed(
            title="Steal",
            description=f"{target.display_name} doesn't have enough money to steal!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    # Simulate theft with a 30% chance of success.
    if random.random() < 0.3:
        stolen = random.randint(10, min(100, victim["balance"] // 3))
        victim["balance"] -= stolen
        thief["balance"] += stolen
        embed = discord.Embed(
            title="Steal",
            description=f"You successfully stole **${stolen}** from **{target.display_name}**!\nYour new balance is **${thief['balance']}**.",
            color=discord.Color.green()
        )
    else:
        fine = random.randint(5, 20)
        thief["balance"] = max(0, thief["balance"] - fine)
        embed = discord.Embed(
            title="Steal",
            description=f"You got caught trying to steal from **{target.display_name}**!\nYou were fined **${fine}**.\nYour new balance is **${thief['balance']}**.",
            color=discord.Color.red()
        )
    await interaction.response.send_message(embed=embed)

@app_commands.command(name="shop", description="View shop items or buy an item.")
@app_commands.describe(item="The item you wish to buy (optional). Leave empty to view available items.")
async def shop(interaction: discord.Interaction, item: Optional[str] = None):
    account = get_account(interaction.user.id)
    if item is None:
        items_list = "\n".join([f"{name.title()} - ${price}" for name, price in SHOP_ITEMS.items()])
        embed = discord.Embed(
            title="Shop - Available Items",
            description=items_list,
            color=discord.Color.blue()
        )
        embed.set_footer(text="To buy an item, use /shop <item>")
        await interaction.response.send_message(embed=embed)
    else:
        item_key = item.lower()
        if item_key not in [key.lower() for key in SHOP_ITEMS]:
            embed = discord.Embed(
                title="Shop",
                description="That item is not available in the shop!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        # Find the actual key (preserving case) from the shop items.
        for key in SHOP_ITEMS:
            if key.lower() == item_key:
                item_key = key
                break

        price = SHOP_ITEMS[item_key]
        if account["balance"] < price:
            embed = discord.Embed(
                title="Shop",
                description="You don't have enough money to buy that item!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return

        account["balance"] -= price
        account["inventory"].append(item_key.lower())
        embed = discord.Embed(
            title="Shop",
            description=f"You bought a **{item_key.title()}** for **${price}**.\nYour new balance is **${account['balance']}**.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)

@app_commands.command(name="gamble", description="Gamble a certain amount of money in a coin flip!")
@app_commands.describe(amount="The amount of money you want to gamble.")
async def gamble(interaction: discord.Interaction, amount: int):
    account = get_account(interaction.user.id)
    if amount <= 0:
        embed = discord.Embed(
            title="Gamble",
            description="You must gamble a positive amount!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    if account["balance"] < amount:
        embed = discord.Embed(
            title="Gamble",
            description="You don't have that much money!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    if random.choice([True, False]):
        account["balance"] += amount
        embed = discord.Embed(
            title="Gamble",
            description=f"You won! You earned an extra **${amount}**.\nYour new balance is **${account['balance']}**.",
            color=discord.Color.green()
        )
    else:
        account["balance"] -= amount
        embed = discord.Embed(
            title="Gamble",
            description=f"You lost the gamble and lost **${amount}**.\nYour new balance is **${account['balance']}**.",
            color=discord.Color.red()
        )
    await interaction.response.send_message(embed=embed)

# ------------------- Admin Commands -------------------

@app_commands.command(name="invedit", description="Admin: Add or remove a shop item from a user's inventory.")
@app_commands.describe(
    user="The target user whose inventory you want to edit.",
    item="The shop item to add or remove.",
    action="Specify 'add' to add the item or 'take' to remove it."
)
async def invedit(interaction: discord.Interaction, user: discord.Member, item: str, action: str):
    # Check if the command user has administrator permissions.
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="Invedit",
            description="You do not have permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Perform a case-insensitive lookup in the shop items.
    shop_item_key = None
    for key in SHOP_ITEMS:
        if key.lower() == item.lower():
            shop_item_key = key
            break

    if shop_item_key is None:
        embed = discord.Embed(
            title="Invedit",
            description="This item does not exist in the shop.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    # Retrieve account for the target user.
    account = get_account(user.id)
    shop_item = shop_item_key.lower()  # use consistent lowercase in the inventory

    if action.lower() == "add":
        account["inventory"].append(shop_item)
        embed = discord.Embed(
            title="Invedit",
            description=f"Added **{shop_item}** to **{user.display_name}**'s inventory.",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed)
    elif action.lower() == "take":
        if shop_item in account["inventory"]:
            account["inventory"].remove(shop_item)
            embed = discord.Embed(
                title="Invedit",
                description=f"Removed **{shop_item}** from **{user.display_name}**'s inventory.",
                color=discord.Color.green()
            )
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="Invedit",
                description=f"**{user.display_name}** does not have **{shop_item}** in their inventory.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        embed = discord.Embed(
            title="Invedit",
            description="Invalid action. Use 'add' or 'take'.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

@app_commands.command(name="moneyedit", description="Admin: Edit a user's balance.")
@app_commands.describe(
    user="The target user whose balance you want to modify.",
    amount="The amount to add (or subtract if negative)."
)
async def moneyedit(interaction: discord.Interaction, user: discord.Member, amount: int):
    # Check if the command user has administrator permissions.
    if not interaction.user.guild_permissions.administrator:
        embed = discord.Embed(
            title="Moneyedit",
            description="You do not have permission to use this command.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    account = get_account(user.id)
    account["balance"] += amount
    embed = discord.Embed(
        title="Moneyedit",
        description=f"**{user.display_name}**'s new balance is **${account['balance']}**.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

class ConfirmView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()

@app_commands.command(name="airstrike", description="Call in a tactical airstrike on a user.")
@app_commands.describe(target="The user to call the airstrike on.")
async def airstrike(interaction: discord.Interaction, target: discord.Member):
    account = get_account(interaction.user.id)
    if account["balance"] < 50000:
        embed = discord.Embed(
            title="Airstrike",
            description="You don't have enough money to call in an airstrike! It costs $50,000.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed)
        return

    view = ConfirmView()
    embed = discord.Embed(
        title="Airstrike Confirmation",
        description=f"Are you sure you want to call an airstrike on **{target.display_name}**? This will cost $50,000 and reset their balance to $100.",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed, view=view)

    await view.wait()
    if view.value is None:
        embed = discord.Embed(
            title="Airstrike",
            description="Airstrike cancelled due to timeout.",
            color=discord.Color.gray()
        )
        await interaction.followup.send(embed=embed)
    elif view.value:
        account["balance"] -= 50000
        target_account = get_account(target.id)
        target_account["balance"] = 100
        embed = discord.Embed(
            title="Airstrike",
            description=f"Airstrike called on **{target.display_name}**! Their balance has been reset to $100.",
            color=discord.Color.green()
        )
        await interaction.followup.send(embed=embed)
    else:
        embed = discord.Embed(
            title="Airstrike",
            description="Airstrike cancelled.",
            color=discord.Color.red()
        )
        await interaction.followup.send(embed=embed)

# ------------------- Setup Function -------------------

async def setup(bot: commands.Bot):
    # Register all commands to the bot's command tree.
    bot.tree.add_command(work)
    bot.tree.add_command(sell)
    bot.tree.add_command(steal)
    bot.tree.add_command(shop)
    bot.tree.add_command(gamble)
    bot.tree.add_command(invedit)
    bot.tree.add_command(moneyedit)
    bot.tree.add_command(airstrike)
