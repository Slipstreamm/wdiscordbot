import discord
from discord import app_commands
from discord.ext import commands
import random
from typing import Optional

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


economy = {}

def get_account(user_id: int) -> dict:
    """Creates an account for the user if one does not exist and returns it."""
    if user_id not in economy:
        economy[user_id] = {"balance": 100, "inventory": []}
    return economy[user_id]

@app_commands.command(name="work", description="Work a job and earn money!")
async def work(interaction: discord.Interaction):
    account = get_account(interaction.user.id)
    earned = random.randint(50, 150)
    job = random.choice(["barista", "cashier", "developer", "bartender", "freelancer"])
    account["balance"] += earned
    await interaction.response.send_message(
        f"You worked as a {job} and earned ${earned}.\nYour new balance is ${account['balance']}."
    )

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

@sell.autocomplete("item")
async def sell_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    account = get_account(interaction.user.id)
    # Use set to get unique items from inventory, as duplicates might exist
    # Items in inventory are stored with original casing from SHOP_ITEMS
    inventory_items = list(set(account.get("inventory", []))) 
    choices = [
        app_commands.Choice(name=item_name.title(), value=item_name)
        for item_name in inventory_items
        if current.lower() in item_name.lower()
    ]
    return choices[:25] # Discord limits to 25 choices

@app_commands.command(name="steal", description="Attempt to steal money from another user!")
@app_commands.describe(target="The member you want to steal from.")
async def steal(interaction: discord.Interaction, target: discord.Member):
    account = get_account(interaction.user.id)
    thief = account
    victim = get_account(target.id)
    if target.id == interaction.user.id:
        await interaction.response.send_message("You can't steal from yourself!")
        return

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

@app_commands.command(name="shop", description="View shop items or buy an item.")
@app_commands.describe(item="The item you wish to buy (optional). Leave empty to view available items.")
async def shop(interaction: discord.Interaction, item: Optional[str] = None):
    account = get_account(interaction.user.id)
    if item is None:
        # List all available shop items.
        items_list = "\n".join([f"{name.title()} - ${price}" for name, price in SHOP_ITEMS.items()])
        response = f"**Available Items:**\n{items_list}\n\nTo buy an item, use `/shop <item>`."
        await interaction.response.send_message(response)
    else:
        # 'item' will be the exact key from SHOP_ITEMS if selected from autocomplete
        # If typed, we still need to find the correct key.
        chosen_item_key = None
        if item in SHOP_ITEMS: # Direct match (e.g., from autocomplete)
            chosen_item_key = item
        else: # Case-insensitive search for typed input
            for key_in_shop in SHOP_ITEMS:
                if key_in_shop.lower() == item.lower():
                    chosen_item_key = key_in_shop
                    break
        
        if not chosen_item_key:
            await interaction.response.send_message("That item is not available in the shop!")
            return

        price = SHOP_ITEMS[chosen_item_key]
        if account["balance"] < price:
            await interaction.response.send_message("You don't have enough money to buy that item!")
            return
        
        account["balance"] -= price
        account["inventory"].append(chosen_item_key)  # Store with original casing
        await interaction.response.send_message(
            f"You bought a {chosen_item_key.title()} for ${price}.\nYour new balance is ${account['balance']}."
        )

@shop.autocomplete("item")
async def shop_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    choices = [
        app_commands.Choice(name=item_name.title() + f" (${item_price})", value=item_name)
        for item_name, item_price in SHOP_ITEMS.items()
        if current.lower() in item_name.lower()
    ]
    # Discord limits to 25 choices
    return choices[:25]

@app_commands.command(name="gamble", description="Gamble a certain amount of money in a coin flip!")
@app_commands.describe(amount="The amount of money you want to gamble.")
async def gamble(interaction: discord.Interaction, amount: int):
    account = get_account(interaction.user.id)
    if amount <= 0:
        await interaction.response.send_message("You must gamble a positive amount!")
        return

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

# ---------- New Admin Commands ----------

@app_commands.command(name="invedit", description="Admin: Add or remove a shop item from a user's inventory.")
@app_commands.describe(
    user="The target user whose inventory you want to edit.",
    item="The shop item to add or remove.",
    action="Specify 'add' to add the item or 'take' to remove it."
)
async def invedit(interaction: discord.Interaction, user: discord.Member, item: str, action: str):
    # Check if the command user has administrator permissions.
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    # 'item' will be the exact key from SHOP_ITEMS if selected from autocomplete.
    # If typed, we still need to find the correct key.
    chosen_item_key = None
    if item in SHOP_ITEMS: # Direct match (e.g., from autocomplete)
        chosen_item_key = item
    else: # Case-insensitive search for typed input
        for key_in_shop in SHOP_ITEMS:
            if key_in_shop.lower() == item.lower():
                chosen_item_key = key_in_shop
                break
    
    if not chosen_item_key:
        await interaction.response.send_message("This item does not exist in the shop.", ephemeral=True)
        return

    account = get_account(user.id)
    # Use the original casing for adding/removing from inventory, consistent with how /shop adds items
    item_to_modify = chosen_item_key 

    if action.lower() == "add":
        account["inventory"].append(item_to_modify)
        await interaction.response.send_message(f"Added {item_to_modify.title()} to {user.display_name}'s inventory.")
    elif action.lower() == "take":
        # When taking, we need to find the item in inventory.
        # Inventory items are stored with original casing.
        item_found_in_inventory = None
        for inv_item in account["inventory"]:
            # Compare with original casing first, then try lowercase if not found (though ideally all are cased)
            if inv_item == item_to_modify:
                 item_found_in_inventory = inv_item
                 break
        # Fallback to case-insensitive if direct match failed (e.g. item was added manually before casing consistency)
        if not item_found_in_inventory:
            for inv_item in account["inventory"]:
                if inv_item.lower() == item_to_modify.lower():
                    item_found_in_inventory = inv_item
                    break

        if item_found_in_inventory:
            account["inventory"].remove(item_found_in_inventory)
            await interaction.response.send_message(f"Removed {item_found_in_inventory.title()} from {user.display_name}'s inventory.")
        else:
            await interaction.response.send_message(f"{user.display_name} does not have {item_to_modify.title()} in their inventory.", ephemeral=True)
    else:
        await interaction.response.send_message("Invalid action. Use 'add' or 'take'.", ephemeral=True)

@invedit.autocomplete("item")
async def invedit_item_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    choices = [
        app_commands.Choice(name=item_name.title() + f" (${item_price})", value=item_name)
        for item_name, item_price in SHOP_ITEMS.items()
        if current.lower() in item_name.lower()
    ]
    return choices[:25]

@invedit.autocomplete("action")
async def invedit_action_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    actions = ["add", "take"]
    choices = [
        app_commands.Choice(name=action_name.title(), value=action_name)
        for action_name in actions
        if current.lower() in action_name.lower()
    ]
    return choices

@app_commands.command(name="moneyedit", description="Admin: Edit a user's balance.")
@app_commands.describe(
    user="The target user whose balance you want to modify.",
    amount="The amount to add (or subtract if negative)."
)
async def moneyedit(interaction: discord.Interaction, user: discord.Member, amount: int):
    # Check if the command user has administrator permissions.
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    account = get_account(user.id)
    account["balance"] += amount
    await interaction.response.send_message(f"{user.display_name}'s new balance is ${account['balance']}.")

# ---------- Setup Function to Register Commands ----------

async def setup(bot: commands.Bot):
    # Register all commands to the bot's command tree.
    bot.tree.add_command(work)
    bot.tree.add_command(sell)
    bot.tree.add_command(steal)
    bot.tree.add_command(shop)
    bot.tree.add_command(gamble)
    bot.tree.add_command(invedit)
    bot.tree.add_command(moneyedit)
