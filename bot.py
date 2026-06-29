import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import View, Select, Button
import os
import json
import random
import asyncio
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

# ===========================================
# DATABASE
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
    description="Add a vouch to a user (staff only)"
)
@app_commands.checks.has_role(TRAINING_ROLE_ID)
async def vouch_add(interaction: discord.Interaction, user: discord.Member):

    add_vouch(user.id)

    count = get_vouches(user.id)

    await interaction.response.send_message(
        embed=success_embed(
            "Vouch Added",
            f"{user.mention} now has **{count} vouches**."
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
        description=f"**User:** {user.mention}\n**Total Vouches:** `{count}`",
        color=discord.Color.blurple(),
        timestamp=datetime.utcnow()
    )

    embed.set_footer(text="Vouch System")

    await interaction.response.send_message(embed=embed, ephemeral=True)
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
