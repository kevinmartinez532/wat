import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import View, Select, Button
import os
import json
import random
import asyncio
import math
from datetime import datetime

# ===========================================
# BOT SETUP
# ===========================================

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

tree = bot.tree

# ===========================================
# RAILWAY TOKEN
# ===========================================

TOKEN = os.getenv("TOKEN")

# ===========================================
# IDs
# ===========================================

TRAINING_CATEGORY_ID = 1520578365822861403

TRAINING_ROLE_ID = 1472343485721083915

AUTO_VOUCH_ROLE = 1472343485695918100

AUTO_VOUCHED_BY = 1472343485687267415

VOUCH_CHANNEL = 1519438302996860989

FLOP_CHANNEL = 1519412904418607376

# ===========================================
# DATABASE (VOUCHES)
# ===========================================

DATABASE = "vouches.json"

if not os.path.exists(DATABASE):
    with open(DATABASE, "w") as f:
        json.dump({}, f, indent=4)

def load_database():
    with open(DATABASE, "r") as f:
        return json.load(f)

def save_database(data):
    with open(DATABASE, "w") as f:
        json.dump(data, f, indent=4)

# ===========================================
# VOUCH FUNCTIONS
# ===========================================

def add_vouch(user_id: int):

    data = load_database()

    user = str(user_id)

    if user not in data:
        data[user] = 0

    data[user] += 1

    save_database(data)

def get_vouches(user_id: int):

    data = load_database()

    return data.get(str(user_id), 0)

# ===========================================
# DATABASE (FLOPS)
# ===========================================

FLOPS_DATABASE = "flops.json"

if not os.path.exists(FLOPS_DATABASE):
    with open(FLOPS_DATABASE, "w") as f:
        json.dump([], f, indent=4)

def load_flops():
    with open(FLOPS_DATABASE, "r") as f:
        return json.load(f)

def save_flops(data):
    with open(FLOPS_DATABASE, "w") as f:
        json.dump(data, f, indent=4)

# ===========================================
# FLOP FUNCTIONS
# ===========================================

def add_flop(flopper_id: int, flopper_tag: str, logged_by_id: int, logged_by_tag: str, split: str, notes: str, image_url: str):

    data = load_flops()

    data.append({
        "flopper_id": flopper_id,
        "flopper_tag": flopper_tag,
        "logged_by_id": logged_by_id,
        "logged_by_tag": logged_by_tag,
        "split": split,
        "notes": notes,
        "image_url": image_url,
        "timestamp": datetime.utcnow().timestamp()
    })

    save_flops(data)


PERIOD_LABELS = {
    "day": "Past Day",
    "week": "Past Week",
    "month": "Past Month",
    "all": "All Time"
}

PERIOD_CHOICES = [
    app_commands.Choice(name="Day", value="day"),
    app_commands.Choice(name="Week", value="week"),
    app_commands.Choice(name="Month", value="month"),
    app_commands.Choice(name="All Time", value="all"),
]


def get_period_cutoff(period: str):
    """Returns a unix timestamp cutoff for the given period, or None for all time."""

    now = datetime.utcnow().timestamp()

    if period == "day":
        return now - 60 * 60 * 24

    elif period == "week":
        return now - 60 * 60 * 24 * 7

    elif period == "month":
        return now - 60 * 60 * 24 * 30

    else:
        return None


def filter_flops_by_period(flops, period: str):

    cutoff = get_period_cutoff(period)

    if cutoff is None:
        return flops

    return [f for f in flops if f["timestamp"] >= cutoff]

# ===========================================
# EMBEDS
# ===========================================

def success_embed(title, description):

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.green()
    )

    embed.timestamp = datetime.utcnow()

    embed.set_footer(
        text="Training System"
    )

    return embed

def red_embed(title, description):

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.red()
    )

    embed.timestamp = datetime.utcnow()

    embed.set_footer(
        text="Training System"
    )

    return embed

def blue_embed(title, description):

    embed = discord.Embed(
        title=title,
        description=description,
        color=discord.Color.blurple()
    )

    embed.timestamp = datetime.utcnow()

    embed.set_footer(
        text="Training System"
    )

    return embed

# ===========================================
# HELPER FUNCTIONS
# ===========================================

async def user_has_ticket(guild, user):

    category = guild.get_channel(TRAINING_CATEGORY_ID)

    if category is None:
        return False

    for channel in category.channels:

        if channel.topic == str(user.id):
            return True

    return False


async def create_training_ticket(interaction, training_type):

    guild = interaction.guild

    if await user_has_ticket(guild, interaction.user):

        await interaction.response.send_message(
            embed=red_embed(
                "Ticket Exists",
                "You already have an open training ticket."
            ),
            ephemeral=True
        )
        return

    category = guild.get_channel(TRAINING_CATEGORY_ID)

    trainer_role = guild.get_role(TRAINING_ROLE_ID)

    overwrites = {

        guild.default_role: discord.PermissionOverwrite(
            view_channel=False
        ),

        interaction.user: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True
        ),

        trainer_role: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            manage_channels=True,
            read_message_history=True
        )

    }

    channel = await guild.create_text_channel(

        name=f"{training_type}-{interaction.user.name}",

        category=category,

        overwrites=overwrites,

        topic=str(interaction.user.id)

    )

    embed = blue_embed(

        "📚 Training Ticket",

        f"""
Welcome {interaction.user.mention}!

A trainer will be with you shortly.

### Training Type
**{training_type.title()}**

Please explain exactly what you need help with.

Use the buttons below to manage this ticket.
"""

    )

    await channel.send(
        content=f"{interaction.user.mention} <@&{TRAINING_ROLE_ID}>",
        embed=embed,
        view=TicketButtons()
    )

    await interaction.response.send_message(

        embed=success_embed(

            "Ticket Created",

            f"Your {training_type} training ticket has been created."

        ),

        ephemeral=True

    )
    # ===========================================
# TICKET BUTTONS
# ===========================================

class TicketButtons(View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Claim",
        style=discord.ButtonStyle.green,
        emoji="🙋",
        custom_id="claim_training_ticket"
    )
    async def claim_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        trainer = interaction.guild.get_role(TRAINING_ROLE_ID)

        if trainer not in interaction.user.roles:

            await interaction.response.send_message(

                "Only trainers can claim tickets.",

                ephemeral=True

            )

            return

        await interaction.channel.send(

            embed=success_embed(

                "Ticket Claimed",

                f"{interaction.user.mention} is now handling this training ticket."

            )

        )

        button.disabled = True

        button.label = f"Claimed by {interaction.user.display_name}"

        await interaction.response.edit_message(

            view=self

        )

    @discord.ui.button(

        label="Close",

        style=discord.ButtonStyle.red,

        emoji="🔒",

        custom_id="close_training_ticket"

    )

    async def close_ticket(

        self,

        interaction: discord.Interaction,

        button: discord.ui.Button

    ):

        trainer = interaction.guild.get_role(TRAINING_ROLE_ID)

        if trainer not in interaction.user.roles and interaction.user.id != int(interaction.channel.topic):

            await interaction.response.send_message(

                "You cannot close this ticket.",

                ephemeral=True

            )

            return

        await interaction.response.send_message(

            embed=red_embed(

                "Closing Ticket",

                "This ticket will close in **5 seconds.**"

            )

        )

        await asyncio.sleep(5)

        await interaction.channel.delete()

# ===========================================
# TRAINING SELECT
# ===========================================

class TrainingDropdown(Select):

    def __init__(self):

        options = [

            discord.SelectOption(

                label="Hitting",

                emoji="🎯",

                description="Learn how to hit."

            ),

            discord.SelectOption(

                label="Recruiting",

                emoji="👥",

                description="Learn how to recruit."

            ),

            discord.SelectOption(

                label="Middleman",

                emoji="⚖️",

                description="Learn how to middleman."

            )

        ]

        super().__init__(

            placeholder="Select a training category...",

            min_values=1,

            max_values=1,

            options=options,

            custom_id="training_dropdown"

        )

    async def callback(self, interaction: discord.Interaction):

        choice = self.values[0].lower()

        if choice == "middleman":
            choice = "middleman"

        elif choice == "hitting":
            choice = "hitting"

        elif choice == "recruiting":
            choice = "recruiting"

        await create_training_ticket(

            interaction,

            choice

        )

# ===========================================
# TRAINING PANEL VIEW
# ===========================================

class TrainingPanel(View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(

            TrainingDropdown()

        )
        # ===========================================
# /SETUPTUTORIAL
# ===========================================

@tree.command(
    name="setuptutorial",
    description="Setup the Training Tutorial panel."
)
@app_commands.checks.has_role(TRAINING_ROLE_ID)
async def setuptutorial(interaction: discord.Interaction):

    embed = discord.Embed(
        title="📚 Training Center",
        description=(
            "**Need help hitting, recruiting, or becoming a middleman?**\n\n"
            "Open a private training ticket using the menu below and one of our "
            "trainers will assist you as soon as possible.\n\n"
            "**Training Categories**\n"
            "🎯 **Hitting**\n"
            "> Learn how to hit efficiently.\n\n"
            "👥 **Recruiting**\n"
            "> Learn how to recruit members successfully.\n\n"
            "⚖️ **Middleman**\n"
            "> Learn how to become a trusted middleman.\n\n"
            "> Please only create a ticket if you genuinely need assistance."
        ),
        color=discord.Color.blurple()
    )

    embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else discord.Embed.Empty)

    embed.set_footer(
        text="Training System • Select a category below."
    )

    embed.timestamp = datetime.utcnow()

    await interaction.channel.send(
        embed=embed,
        view=TrainingPanel()
    )

    await interaction.response.send_message(
        embed=success_embed(
            "Training Panel Created",
            "The training panel has been successfully posted."
        ),
        ephemeral=True
    )

# ===========================================
# ERROR HANDLER
# ===========================================

@setuptutorial.error
async def setup_error(interaction: discord.Interaction, error):

    if isinstance(error, app_commands.MissingRole):

        await interaction.response.send_message(
            embed=red_embed(
                "Missing Permission",
                "You do not have permission to use this command."
            ),
            ephemeral=True
        )
        # ===========================================
# VOUCH SYSTEM COMMANDS
# ===========================================

@tree.command(
    name="vouch",
    description="Vouch for a user"
)
async def vouch(interaction: discord.Interaction, user: discord.Member):

    add_vouch(user.id)

    count = get_vouches(user.id)

    channel = bot.get_channel(VOUCH_CHANNEL)

    if channel:

        embed = discord.Embed(
            title="✅ New Vouch",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )

        embed.add_field(
            name="Vouched Member",
            value=user.mention,
            inline=True
        )

        embed.add_field(
            name="Vouched By",
            value=interaction.user.mention,
            inline=True
        )

        embed.add_field(
            name="Total Vouches",
            value=str(count),
            inline=False
        )

        embed.set_footer(text="Vouch System")

        await channel.send(embed=embed)

    await interaction.response.send_message(
        embed=success_embed(
            "Vouch Sent",
            f"You successfully vouched {user.mention}."
        ),
        ephemeral=True
    )


@tree.command(
    name="vouch_add",
    description="Add vouches to a user (staff only)"
)
@app_commands.checks.has_role(TRAINING_ROLE_ID)
async def vouch_add(
    interaction: discord.Interaction,
    user: discord.Member,
    amount: int
):

    if amount <= 0:
        await interaction.response.send_message(
            embed=red_embed(
                "Invalid Amount",
                "You must add at least 1 vouch."
            ),
            ephemeral=True
        )
        return

    data = load_database()
    uid = str(user.id)

    if uid not in data:
        data[uid] = 0

    data[uid] += amount
    save_database(data)

    count = data[uid]

    await interaction.response.send_message(
        embed=success_embed(
            "Vouches Added",
            f"{user.mention} received **+{amount} vouches**\n"
            f"Total now: **{count}**"
        ),
        ephemeral=True
    )


@tree.command(
    name="vouchcount",
    description="Check a user's vouch count"
)
async def vouchcount(interaction: discord.Interaction, user: discord.Member):

    count = get_vouches(user.id)

    embed = discord.Embed(
        title="📊 Vouch Count",
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow()
    )

    embed.add_field(
        name="User",
        value=user.mention,
        inline=True
    )

    embed.add_field(
        name="Total Vouches",
        value=f"**{count}**",
        inline=True
    )

    embed.set_footer(text="Vouch System")

    await interaction.response.send_message(embed=embed)
    # ===========================================
# PAGINATED VIEW (used by flop leaderboard / history)
# ===========================================

class PaginatedView(View):

    def __init__(self, embeds: list, author_id: int):

        super().__init__(timeout=60)

        self.embeds = embeds
        self.page = 0
        self.author_id = author_id
        self.message = None

        self.update_buttons()

    def update_buttons(self):

        self.back_button.disabled = self.page <= 0
        self.next_button.disabled = self.page >= len(self.embeds) - 1

    @discord.ui.button(label="◀ Back", style=discord.ButtonStyle.grey, custom_id="flop_page_back")
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.author_id:

            await interaction.response.send_message(
                "Only the person who ran this command can page through it.",
                ephemeral=True
            )
            return

        self.page = max(0, self.page - 1)

        self.update_buttons()

        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.grey, custom_id="flop_page_next")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.author_id:

            await interaction.response.send_message(
                "Only the person who ran this command can page through it.",
                ephemeral=True
            )
            return

        self.page = min(len(self.embeds) - 1, self.page + 1)

        self.update_buttons()

        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    async def on_timeout(self):

        for child in self.children:
            child.disabled = True

        if self.message:

            try:
                await self.message.edit(view=self)
            except Exception:
                pass

# ===========================================
# FLOP SYSTEM COMMANDS
# ===========================================

@tree.command(
    name="flop",
    description="Log a flop against a trader"
)
@app_commands.describe(
    flopper="The user who flopped",
    split="What the split was",
    image="Required proof (mercy screenshot or in-game screenshot)",
    notes="Optional extra notes"
)
async def flop(
    interaction: discord.Interaction,
    flopper: discord.Member,
    split: str,
    image: discord.Attachment,
    notes: str = None
):

    if not image.content_type or not image.content_type.startswith("image/"):

        await interaction.response.send_message(
            embed=red_embed(
                "Invalid Image",
                "The attached file must be an image (mercy screenshot or in-game screenshot)."
            ),
            ephemeral=True
        )
        return

    notes_display = notes if notes else "None"

    add_flop(
        flopper_id=flopper.id,
        flopper_tag=str(flopper),
        logged_by_id=interaction.user.id,
        logged_by_tag=str(interaction.user),
        split=split,
        notes=notes_display,
        image_url=image.url
    )

    channel = bot.get_channel(FLOP_CHANNEL)

    if channel:

        embed = discord.Embed(
            title="🚩 Flop Logged",
            description="A new flop has been logged.",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )

        embed.add_field(
            name="👤 Flopper",
            value=flopper.mention,
            inline=False
        )

        embed.add_field(
            name="✂️ Split",
            value=split,
            inline=False
        )

        embed.add_field(
            name="📝 Extra Notes",
            value=notes_display,
            inline=False
        )

        embed.set_image(url=image.url)

        embed.set_footer(text="Grow A Garden 2 | MM Services")

        await channel.send(embed=embed)

    await interaction.response.send_message(
        embed=success_embed(
            "Flop Logged",
            f"Flop logged against {flopper.mention} in <#{FLOP_CHANNEL}>."
        ),
        ephemeral=True
    )


@tree.command(
    name="flopcount",
    description="Shows the total number of flops logged in a period"
)
@app_commands.describe(period="Time period")
@app_commands.choices(period=PERIOD_CHOICES)
async def flopcount(interaction: discord.Interaction, period: app_commands.Choice[str]):

    data = load_flops()

    filtered = filter_flops_by_period(data, period.value)

    count = len(filtered)

    embed = discord.Embed(
        title=f"🚩 Total Server Flops ({PERIOD_LABELS[period.value]})",
        description=f"There {'is' if count == 1 else 'are'} **{count}** total flop(s) logged in the server.",
        color=discord.Color.red(),
        timestamp=datetime.utcnow()
    )

    embed.set_footer(text="Grow A Garden 2 | MM Services")

    await interaction.response.send_message(embed=embed)


@tree.command(
    name="floplb",
    description="Shows the flop leaderboard for a period"
)
@app_commands.describe(period="Time period")
@app_commands.choices(period=PERIOD_CHOICES)
async def floplb(interaction: discord.Interaction, period: app_commands.Choice[str]):

    data = load_flops()

    filtered = filter_flops_by_period(data, period.value)

    counts = {}

    for entry in filtered:

        fid = entry["flopper_id"]

        counts[fid] = counts.get(fid, 0) + 1

    rows = sorted(counts.items(), key=lambda item: item[1], reverse=True)

    if not rows:

        embed = discord.Embed(
            title=f"🚩 Flop Leaderboard ({PERIOD_LABELS[period.value]})",
            description="No flops logged for this period.",
            color=discord.Color.red()
        )

        embed.set_footer(text="Grow A Garden 2 | MM Services")

        await interaction.response.send_message(embed=embed)
        return

    per_page = 10

    total_pages = math.ceil(len(rows) / per_page)

    embeds = []

    for page in range(total_pages):

        chunk = rows[page * per_page: page * per_page + per_page]

        lines = []

        for i, (flopper_id, cnt) in enumerate(chunk, start=page * per_page + 1):

            lines.append(f"{i}. <@{flopper_id}> — {cnt} flop{'' if cnt == 1 else 's'}")

        embed = discord.Embed(
            title=f"🚩 Flop Leaderboard ({PERIOD_LABELS[period.value]})",
            description="\n".join(lines),
            color=discord.Color.red()
        )

        embed.set_footer(text=f"Grow A Garden 2 | MM Services • Page {page + 1}/{total_pages}")

        embeds.append(embed)

    view = PaginatedView(embeds, interaction.user.id) if total_pages > 1 else None

    await interaction.response.send_message(embed=embeds[0], view=view)

    if view:
        view.message = await interaction.original_response()


@tree.command(
    name="viewflops",
    description="Shows a user's flop history for a period"
)
@app_commands.describe(user="The user to look up", period="Time period")
@app_commands.choices(period=PERIOD_CHOICES)
async def viewflops(interaction: discord.Interaction, user: discord.Member, period: app_commands.Choice[str]):

    data = load_flops()

    user_flops = [f for f in data if f["flopper_id"] == user.id]

    filtered = filter_flops_by_period(user_flops, period.value)

    filtered.sort(key=lambda f: f["timestamp"], reverse=True)

    if not filtered:

        embed = discord.Embed(
            title=f"🚩 Flop History — {user.display_name}",
            description=f"No flops logged for this user ({PERIOD_LABELS[period.value]}).",
            color=discord.Color.red()
        )

        embed.set_footer(text="Grow A Garden 2 | MM Services")

        await interaction.response.send_message(embed=embed)
        return

    per_page = 5

    total_pages = math.ceil(len(filtered) / per_page)

    embeds = []

    for page in range(total_pages):

        chunk = filtered[page * per_page: page * per_page + per_page]

        embed = discord.Embed(
            title=f"🚩 Flop History — {user.display_name}",
            description=f"**{len(filtered)}** flop(s) logged ({PERIOD_LABELS[period.value]})",
            color=discord.Color.red()
        )

        for entry in chunk:

            ts = int(entry["timestamp"])

            embed.add_field(
                name=f"<t:{ts}:f>",
                value=(
                    f"✂️ Split: {entry['split']}\n"
                    f"📝 Notes: {entry['notes']}\n"
                    f"👮 Logged by: <@{entry['logged_by_id']}>"
                ),
                inline=False
            )

        embed.set_footer(text=f"Grow A Garden 2 | MM Services • Page {page + 1}/{total_pages}")

        embeds.append(embed)

    view = PaginatedView(embeds, interaction.user.id) if total_pages > 1 else None

    await interaction.response.send_message(embed=embeds[0], view=view)

    if view:
        view.message = await interaction.original_response()

# ===========================================
# AUTO VOUCH SYSTEM
# ===========================================

@tasks.loop(minutes=10)
async def auto_vouch_task():

    await bot.wait_until_ready()

    guild = None

    # get first guild bot is in
    for g in bot.guilds:
        guild = g
        break

    if guild is None:
        return

    role = guild.get_role(AUTO_VOUCH_ROLE)
    voucher_role = guild.get_role(AUTO_VOUCHED_BY)

    if not role or not voucher_role:
        return

    members = [m for m in role.members if not m.bot]

    if len(members) == 0:
        return

    user = random.choice(members)

    add_vouch(user.id)

    count = get_vouches(user.id)

    channel = bot.get_channel(VOUCH_CHANNEL)

    if channel:

        embed = discord.Embed(
            title="🤖 Auto Vouch",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow()
        )

        embed.add_field(
            name="Vouched Member",
            value=user.mention,
            inline=True
        )

        embed.add_field(
            name="Vouched By",
            value=f"<@&{AUTO_VOUCHED_BY}>",
            inline=True
        )

        embed.add_field(
            name="Total Vouches",
            value=str(count),
            inline=False
        )

        embed.set_footer(text="Auto Vouch System")

        await channel.send(embed=embed)


# randomize interval (10–15 min)
@auto_vouch_task.before_loop
async def before_auto_vouch():

    await bot.wait_until_ready()

    while True:

        wait_time = random.randint(600, 900)  # 10–15 min

        await asyncio.sleep(wait_time)


# ===========================================
# START TASK ON READY
# ===========================================

@bot.event
async def on_ready():

    print(f"Logged in as {bot.user}")

    try:
        await tree.sync()
        print("Slash commands synced")
    except Exception as e:
        print(e)

    if not auto_vouch_task.is_running():
        auto_vouch_task.start()
        # ===========================================
# PERSISTENT VIEWS (IMPORTANT)
# ===========================================

@bot.event
async def setup_hook():

    # Register persistent views so dropdown/buttons still work after restart
    bot.add_view(TrainingPanel())
    bot.add_view(TicketButtons())


# ===========================================
# SAFETY: GLOBAL ERROR HANDLER
# ===========================================

@bot.tree.error
async def on_app_command_error(interaction: discord.Interaction, error):

    if isinstance(error, app_commands.MissingRole):

        if interaction.response.is_done():

            await interaction.followup.send(
                embed=red_embed(
                    "Missing Permission",
                    "You do not have permission to use this command."
                ),
                ephemeral=True
            )
        else:

            await interaction.response.send_message(
                embed=red_embed(
                    "Missing Permission",
                    "You do not have permission to use this command."
                ),
                ephemeral=True
            )

    else:

        print(f"Unhandled error: {error}")


# ===========================================
# RUN BOT (RAILWAY TOKEN)
# ===========================================

if __name__ == "__main__":

    if TOKEN is None:

        print("ERROR: TOKEN not found in environment variables.")

    else:

        bot.run(TOKEN)
