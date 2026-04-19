import discord
from discord.ext import commands
import json, os, time, random, asyncio

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="-", intents=intents, help_command=None)

DATA_FILE = "data.json"

HEAD_ADMIN_ROLE = "Head Admin"

# CHANNELS
SPIN_CHANNEL_ID = 1495430732133306471
ADMIN_ABUSE_CHANNEL_ID = 1494848274354671616
TICKET_CHANNEL_ID = 1495430880305483786
TICKET_CATEGORY_ID = 1495459648877367437

LEB_ID = 1209628287379447860

SPIN_COOLDOWN = 10

# ================= DATA =================

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def get_user(data, uid):
    uid = str(uid)
    if uid not in data:
        data[uid] = {"coins": 0, "spins": 0, "luck_until": 0}
    else:
        data[uid].setdefault("coins", 0)
        data[uid].setdefault("spins", 0)
        data[uid].setdefault("luck_until", 0)
    return data[uid]

def is_head_admin(member):
    return any(r.name == HEAD_ADMIN_ROLE for r in member.roles)

def check_spin_channel(ctx):
    return ctx.channel.id == SPIN_CHANNEL_ID

# ================= READY =================

@bot.event
async def on_ready():
    print(f"{bot.user} is online!")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        if ctx.command and ctx.command.name == "spin":
            await ctx.send(f"⏳ You must wait **{round(error.retry_after, 1)} seconds** before using `-spin` again.")
        return

    if isinstance(error, commands.CommandNotFound):
        return

    raise error

# ================= HELP =================

@bot.command()
async def help(ctx):
    await ctx.send(
        "**Commands:**\n"
        "-balance\n"
        "-spin\n"
        "-dailyspin\n"
        "-spincount\n"
        "-shop\n"
        "-pay @user amount\n"
        "-setup_tickets (Head Admin)\n"
        "-givespin @user amount (Head Admin)\n"
        "-givecoins @user amount (Head Admin)\n"
        "-adminabuse (Head Admin)"
    )

# ================= ECONOMY =================

@bot.command()
async def balance(ctx):
    data = load_data()
    user = get_user(data, ctx.author.id)

    if is_head_admin(ctx.author):
        return await ctx.send("💰 ∞ coins")

    await ctx.send(f"💰 {user['coins']:,} coins")

@bot.command()
async def givecoins(ctx, member: discord.Member, amount: int):
    if not is_head_admin(ctx.author):
        return await ctx.send("❌ Only Head Admin can use this command.")

    if amount <= 0:
        return await ctx.send("❌ Invalid amount.")

    data = load_data()
    get_user(data, member.id)["coins"] += amount
    save_data(data)
    await ctx.send("done")

@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        return await ctx.send("❌ Invalid amount.")

    data = load_data()
    sender = get_user(data, ctx.author.id)
    receiver = get_user(data, member.id)

    if not is_head_admin(ctx.author):
        if sender["coins"] < amount:
            return await ctx.send("not enough")
        sender["coins"] -= amount

    receiver["coins"] += amount
    save_data(data)
    await ctx.send("sent")

# ================= SPIN =================

async def spin_reward(ctx, user):
    boosted = time.time() < user["luck_until"]
    roll = max(random.randint(1, 100), random.randint(1, 100)) if boosted else random.randint(1, 100)

    header = "🔥 **2X LUCK ACTIVE** 🔥\n\n" if boosted else ""

    msg = await ctx.send(f"{header}🎰 **YOU SPUN THE WHEEL!**\n\n🎡 Spinning...")

    fake_rewards = [
        "💰 10,000 Coins",
        "💰 100,000 Coins",
        "✨ 10,000 XP",
        "🔥 100,000 XP",
        "👑 Rare Role",
        "💎 Ultra Rare Role"
    ]

    for _ in range(5):
        await asyncio.sleep(0.4)
        await msg.edit(content=f"{header}🎰 **YOU SPUN THE WHEEL!**\n\n➡️ {random.choice(fake_rewards)}")

    if roll <= 75:
        amount = 10000
        user["coins"] += amount
        result = f"💰 {amount:,} coins"
    elif roll <= 90:
        amount = 100000
        user["coins"] += amount
        result = f"💰 {amount:,} coins"
    elif roll <= 97:
        result = f"✨ 10,000 XP → open ticket <#{TICKET_CHANNEL_ID}>"
    elif roll <= 99:
        result = f"🔥 100,000 XP → open ticket <#{TICKET_CHANNEL_ID}>"
    else:
        result = "💎 rare reward"

    await msg.edit(content=f"{header}🎯 {result}")

@bot.command()
@commands.cooldown(1, SPIN_COOLDOWN, commands.BucketType.user)
async def spin(ctx):
    if not check_spin_channel(ctx):
        return await ctx.send(f"❌ You can only use spin commands in <#{SPIN_CHANNEL_ID}>.")

    data = load_data()
    user = get_user(data, ctx.author.id)

    if user["spins"] <= 0 and not is_head_admin(ctx.author):
        return await ctx.send("no spins")

    if not is_head_admin(ctx.author):
        user["spins"] -= 1

    await spin_reward(ctx, user)
    save_data(data)

@bot.command()
async def dailyspin(ctx):
    if not check_spin_channel(ctx):
        return await ctx.send(f"❌ You can only use spin commands in <#{SPIN_CHANNEL_ID}>.")

    data = load_data()
    user = get_user(data, ctx.author.id)
    user["spins"] += 1
    save_data(data)
    await ctx.send("+1 spin")

@bot.command()
async def spincount(ctx):
    if not check_spin_channel(ctx):
        return await ctx.send(f"❌ You can only use spin commands in <#{SPIN_CHANNEL_ID}>.")

    data = load_data()
    user = get_user(data, ctx.author.id)

    if is_head_admin(ctx.author):
        return await ctx.send("∞ spins")

    await ctx.send(f"{user['spins']}")

@bot.command()
async def givespin(ctx, member: discord.Member, amount: int = 1):
    if not is_head_admin(ctx.author):
        return await ctx.send("❌ Only Head Admin can use this command.")

    if amount <= 0:
        return await ctx.send("❌ Invalid amount.")

    data = load_data()
    get_user(data, member.id)["spins"] += amount
    save_data(data)
    await ctx.send("done")

# ================= SHOP =================

class ExchangeModal(discord.ui.Modal, title="Exchange Ash Coins"):
    amount = discord.ui.TextInput(
        label="How many Ash Coins do you want to exchange?",
        placeholder="Minimum 500",
        required=True,
        max_length=12
    )

    def __init__(self, user):
        super().__init__()
        self.user = user

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ This shop isn't yours.", ephemeral=True)
            return

        raw = str(self.amount).strip()

        if not raw.isdigit():
            await interaction.response.send_message("❌ Enter a valid number.", ephemeral=True)
            return

        amount = int(raw)

        if amount < 500:
            await interaction.response.send_message("❌ Minimum exchange is 500 Ash Coins.", ephemeral=True)
            return

        data = load_data()
        user = get_user(data, interaction.user.id)

        if not is_head_admin(interaction.user):
            if user["coins"] < amount:
                await interaction.response.send_message("❌ Not enough Ash Coins.", ephemeral=True)
                return
            user["coins"] -= amount

        save_data(data)

        await interaction.response.send_message(
            f"✅ Exchange request for **{amount:,} Ash Coins** created.\n"
            f"Open a ticket in <#{TICKET_CHANNEL_ID}> to claim it.",
            ephemeral=True
        )

class ShopView(discord.ui.View):
    def __init__(self, user):
        super().__init__(timeout=180)
        self.user = user

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user != self.user:
            await interaction.response.send_message("❌ This shop isn't yours.", ephemeral=True)
            return False
        return True

    async def spend(self, interaction: discord.Interaction, cost: int):
        data = load_data()
        user = get_user(data, interaction.user.id)

        if not is_head_admin(interaction.user):
            if user["coins"] < cost:
                await interaction.response.send_message("❌ Not enough Ash Coins.", ephemeral=True)
                return None, None
            user["coins"] -= cost

        return data, user

    @discord.ui.button(label="1 Spin (50k)", style=discord.ButtonStyle.primary, row=0)
    async def buy_1_spin(self, interaction: discord.Interaction, button: discord.ui.Button):
        data, user = await self.spend(interaction, 50000)
        if data is None:
            return

        user["spins"] += 1
        save_data(data)
        await interaction.response.send_message("🎟 You bought **1 spin**.", ephemeral=True)

    @discord.ui.button(label="5 Spins (200k)", style=discord.ButtonStyle.primary, row=0)
    async def buy_5_spins(self, interaction: discord.Interaction, button: discord.ui.Button):
        data, user = await self.spend(interaction, 200000)
        if data is None:
            return

        user["spins"] += 5
        save_data(data)
        await interaction.response.send_message("🎟 You bought **5 spins**.", ephemeral=True)

    @discord.ui.button(label="10 Spins (400k)", style=discord.ButtonStyle.primary, row=0)
    async def buy_10_spins(self, interaction: discord.Interaction, button: discord.ui.Button):
        data, user = await self.spend(interaction, 400000)
        if data is None:
            return

        user["spins"] += 10
        save_data(data)
        await interaction.response.send_message("🎟 You bought **10 spins**.", ephemeral=True)

    @discord.ui.button(label="1,000 XP (15k)", style=discord.ButtonStyle.secondary, row=1)
    async def buy_1000_xp(self, interaction: discord.Interaction, button: discord.ui.Button):
        data, user = await self.spend(interaction, 15000)
        if data is None:
            return

        save_data(data)
        await interaction.response.send_message(
            f"✨ You bought **1,000 XP**.\nOpen a ticket in <#{TICKET_CHANNEL_ID}> to claim it.",
            ephemeral=True
        )

    @discord.ui.button(label="10,000 XP (100k)", style=discord.ButtonStyle.secondary, row=1)
    async def buy_10000_xp(self, interaction: discord.Interaction, button: discord.ui.Button):
        data, user = await self.spend(interaction, 100000)
        if data is None:
            return

        save_data(data)
        await interaction.response.send_message(
            f"✨ You bought **10,000 XP**.\nOpen a ticket in <#{TICKET_CHANNEL_ID}> to claim it.",
            ephemeral=True
        )

    @discord.ui.button(label="100,000 XP (750k)", style=discord.ButtonStyle.secondary, row=1)
    async def buy_100000_xp(self, interaction: discord.Interaction, button: discord.ui.Button):
        data, user = await self.spend(interaction, 750000)
        if data is None:
            return

        save_data(data)
        await interaction.response.send_message(
            f"✨ You bought **100,000 XP**.\nOpen a ticket in <#{TICKET_CHANNEL_ID}> to claim it.",
            ephemeral=True
        )

    @discord.ui.button(label="2x Luck (1M)", style=discord.ButtonStyle.success, row=2)
    async def luck(self, interaction: discord.Interaction, button: discord.ui.Button):
        data, user = await self.spend(interaction, 1000000)
        if data is None:
            return

        user["luck_until"] = time.time() + 600
        save_data(data)
        await interaction.response.send_message("🔥 **2x luck** active for **10 minutes**.", ephemeral=True)

    @discord.ui.button(label="Exchange", style=discord.ButtonStyle.success, row=2)
    async def exchange(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ExchangeModal(self.user))

@bot.command()
async def shop(ctx):
    data = load_data()
    u = get_user(data, ctx.author.id)

    coins_text = "∞" if is_head_admin(ctx.author) else f"{u['coins']:,}"

    embed = discord.Embed(title="🛒 Shop")
    embed.description = f"coins: {coins_text}"

    await ctx.send(embed=embed, view=ShopView(ctx.author))

# ================= TICKETS =================

class TicketView(discord.ui.View):
    @discord.ui.button(label="Create Ticket")
    async def create(self, i, b):
        category = i.guild.get_channel(TICKET_CATEGORY_ID)

        if category is None:
            return await i.response.send_message("❌ Ticket category not found.", ephemeral=True)

        overwrites = {
            i.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            i.user: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        for r in i.guild.roles:
            if r.name in ["Admin", "Head Admin"]:
                overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        ch = await i.guild.create_text_channel(
            f"ticket-{i.user.name}",
            category=category,
            overwrites=overwrites,
            topic=f"ticket_owner:{i.user.id}"
        )

        await ch.send(f"{i.user.mention} help coming")
        await i.response.send_message("created", ephemeral=True)

@bot.command()
async def setup_tickets(ctx):
    if not is_head_admin(ctx.author):
        return await ctx.send("❌ Only Head Admin can use this command.")

    ch = bot.get_channel(TICKET_CHANNEL_ID)
    if ch is None:
        return await ctx.send("❌ Ticket channel not found.")

    await ch.set_permissions(ctx.guild.default_role, send_messages=False)
    await ch.set_permissions(ctx.guild.me, send_messages=True)
    await ch.send("create ticket:", view=TicketView())

# ================= ADMIN ABUSE =================

async def admin_abuse(guild):
    ch = guild.get_channel(ADMIN_ABUSE_CHANNEL_ID)

    if ch is None:
        return

    await ch.set_permissions(guild.default_role, send_messages=False)
    await ch.set_permissions(guild.me, send_messages=True)

    await ch.send(
        f"hello everyone welcome to the weekly admin abuse event this is performed every week on a Saturday around six to eight p.m UK time. "
        f"Here’s a shout out to <@{LEB_ID}> who has made this event possible and how I am here as a bot today so let’s stop fooling around and let me give you your first reward……."
    )

    end = time.time() + 1800

    await run_admin_abuse_reward(guild, ch)

    while time.time() < end:
        await asyncio.sleep(random.randint(160, 200))

        await ch.send(random.choice([
            "Are you ready for what I’m about to drop?",
            "Get ready for this!",
            "You’re not ready for the next one…",
            "Here comes another one!",
            "Let me cook for a second…"
        ]))

        await asyncio.sleep(5)
        await run_admin_abuse_reward(guild, ch)

    await ch.send("🛑 **Admin Abuse ended**")
    await ch.set_permissions(guild.default_role, send_messages=True)
    await ch.set_permissions(guild.me, overwrite=None)

async def run_admin_abuse_reward(guild, ch):
    reward = random.choice(["coins", "spins", "luck", "xp"])
    data = load_data()

    if reward == "coins":
        amount = random.randint(10000, 100000)
        for m in guild.members:
            if not m.bot:
                get_user(data, m.id)["coins"] += amount
        save_data(data)
        await ch.send(f"💰 **ASH COIN RAIN** 💰\n\nEveryone gets **{amount:,} Ash Coins!**")

    elif reward == "spins":
        amount = random.randint(1, 10)
        for m in guild.members:
            if not m.bot:
                get_user(data, m.id)["spins"] += amount
        save_data(data)
        await ch.send(f"🎟 **SPIN STORM** 🎟\n\nEveryone gets **{amount} spins!**")

    elif reward == "luck":
        duration = random.randint(600, 1800)
        minutes = duration // 60
        for m in guild.members:
            if not m.bot:
                get_user(data, m.id)["luck_until"] = int(time.time()) + duration
        save_data(data)
        await ch.send(f"🔥 **2X LUCK FOR EVERYONE** 🔥\n\nEveryone gets **2x luck** for **{minutes} minutes!**")

    else:
        amount = random.randint(10000, 50000)
        await ch.send(
            f"✨ **XP BURST** ✨\n\nEveryone gets **{amount:,} XP!**\n🎟 Create a ticket in <#{TICKET_CHANNEL_ID}> to claim it."
        )

@bot.command()
async def adminabuse(ctx):
    if not is_head_admin(ctx.author):
        return await ctx.send("❌ Only Head Admin can use this command.")

    await ctx.send("⏳ Admin Abuse scheduled in **24 hours**.")
    await asyncio.sleep(86400)
    await admin_abuse(ctx.guild)

bot.run("MTQ5NTA2NDE0MDY1NjU0MTc1OQ.GC_c63.7d-v8mDqS3IXxHgJeEnN7MS4eLLzo2afA3mVyg")