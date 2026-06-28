import discord
from discord.ext import commands
from discord.ui import View, Select, Button
import os
import asyncio

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="$", intents=intents)

GUILD_ID = 1472343485687267408
STAFF_ROLE_ID = 1472343485704310802
TRAINING_CATEGORY_ID = 1520578365822861403

# TRACK OPEN TICKETS
active_tickets = {}


# =========================
# CLOSE BUTTON
# =========================

class CloseTicketButton(Button):
    def __init__(self):
        super().__init__(
            label="Close Ticket",
            style=discord.ButtonStyle.red,
            emoji="🔒"
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Closing ticket in 5 seconds...",
            ephemeral=True
        )

        await asyncio.sleep(5)
        await interaction.channel.delete()


class TicketControlView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CloseTicketButton())


# =========================
# DROPDOWN
# =========================

class TrainingSelect(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Recruiting", emoji="📈"),
            discord.SelectOption(label="Hitting", emoji="🎯"),
            discord.SelectOption(label="Middleman", emoji="🤝"),
        ]

        super().__init__(
            placeholder="Select a training category...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        # prevent spam tickets
        if user.id in active_tickets:
            await interaction.response.send_message(
                "You already have a ticket open.",
                ephemeral=True
            )
            return

        category = guild.get_channel(TRAINING_CATEGORY_ID)

        name = f"{self.values[0].lower()}-{user.name}".replace(" ", "-")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.get_role(STAFF_ROLE_ID): discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True)
        }

        channel = await guild.create_text_channel(
            name=name,
            category=category,
            overwrites=overwrites
        )

        # save ticket
        active_tickets[user.id] = channel.id

        await interaction.response.send_message(
            f"Ticket created: {channel.mention}",
            ephemeral=True
        )

        embed = discord.Embed(
            title="🎓 Training Ticket",
            description=f"{user.mention} selected **{self.values[0]}** training.\nStaff will assist you soon.",
            color=discord.Color.green()
        )

        await channel.send(
            content=f"<@&{STAFF_ROLE_ID}>",
            embed=embed,
            view=TicketControlView()
        )


class TrainingView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TrainingSelect())


# =========================
# PANEL COMMAND
# =========================

@bot.command()
async def panel(ctx):
    if ctx.guild.id != GUILD_ID:
        return

    await ctx.message.delete()

    embed = discord.Embed(
        title="🎓 Training Tickets",
        description="Select a category below to create a training ticket.",
        color=discord.Color.blue()
    )

    await ctx.send(embed=embed, view=TrainingView())


# =========================
# READY EVENT
# =========================

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    bot.add_view(TrainingView())


# =========================
# RUN BOT
# =========================

bot.run(os.getenv("BOT_TOKEN"))
