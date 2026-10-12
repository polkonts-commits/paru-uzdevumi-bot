
import os
import json
import random
from datetime import date
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
DATA_FILE = Path("data.json")

TASKS = [
    "Pasakiet viens otram trīs lietas, ko šodien novērtējat.",
    "Atcerieties vienu kopīgu brīdi, kas jums abiem liek pasmaidīt.",
    "Katrs nosauciet vienu lietu, ko vēlētos kopā izmēģināt.",
    "Uzrakstiet viens otram īsu, patiesu komplimentu.",
    "Pastāstiet, kas jums šonedēļ palīdzētu justies tuvākiem.",
    "Izdomājiet vienu nelielu kopīgu mērķi nākamajām septiņām dienām.",
    "Katrs nosauciet vienu lietu, par kuru esat pateicīgi otram.",
    "Vienojieties par vienu kopīgu aktivitāti nākamajai nedēļai.",
    "Uzdodiet viens otram jautājumu, ko sen gribējāt uzdot.",
    "Atcerieties, kāds bija jūsu pirmais iespaids vienam par otru."
]

def load_data():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"pairs": {}}

data = load_data()

def save_data():
    DATA_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def get_pair_for_user(user_id):
    for pair_id, pair in data["pairs"].items():
        if user_id in pair["members"]:
            return pair_id, pair
    return None, None

class PairInvite(discord.ui.View):
    def __init__(self, inviter, invitee):
        super().__init__(timeout=86400)
        self.inviter = inviter
        self.invitee = invitee

    @discord.ui.button(
        label="Pieņemt uzaicinājumu",
        style=discord.ButtonStyle.success,
        emoji="❤️"
    )
    async def accept(self, interaction, button):
        if interaction.user.id != self.invitee.id:
            await interaction.response.send_message(
                "Šis uzaicinājums ir paredzēts citam cilvēkam.",
                ephemeral=True
            )
            return

        if get_pair_for_user(self.inviter.id)[0] or \
           get_pair_for_user(self.invitee.id)[0]:
            await interaction.response.send_message(
                "Viens no jums jau ir savienots pārī.",
                ephemeral=True
            )
            return

        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message(
                "Šo darbību var veikt tikai serverī.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            self.inviter: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
            self.invitee: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            ),
        }

        category = await guild.create_category(
            f"💞 {self.inviter.display_name} + "
            f"{self.invitee.display_name}",
            overwrites=overwrites
        )

        tasks_channel = await guild.create_text_channel(
            "💞-dienas-uzdevumi", category=category
        )
        history_channel = await guild.create_text_channel(
            "📚-uzdevumu-vesture", category=category
        )

        pair_id = str(category.id)
        data["pairs"][pair_id] = {
            "guild_id": guild.id,
            "members": [self.inviter.id, self.invitee.id],
            "category_id": category.id,
            "tasks_channel_id": tasks_channel.id,
            "history_channel_id": history_channel.id,
            "task_date": "",
            "task_text": "",
            "answers": {},
            "history": []
        }
        save_data()

        await tasks_channel.send(
            f"Sveicināti, {self.inviter.mention} un "
            f"{self.invitee.mention}! ❤️\n"
            "Jūsu privātā pāra telpa ir gatava.\n"
            "Izmantojiet `/task`, lai saņemtu dienas uzdevumu, "
            "un `/answer`, lai iesniegtu atbildi."
        )
        await history_channel.send(
            "📚 Šeit glabāsies jūsu iepriekšējo uzdevumu un "
            "atbilžu vēsture."
        )
        await interaction.followup.send(
            "Uzaicinājums pieņemts! Jūsu privātā telpa ir izveidota.",
            ephemeral=True
        )
        self.stop()

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Bot: {bot.user} | Sinhronizētas {len(synced)} komandas")
    except Exception as error:
        print(f"Komandu sinhronizācijas kļūda: {error}")

@bot.tree.command(
    name="pair_invite",
    description="Uzaicini partneri izveidot privātu pāra telpu"
)
@app_commands.describe(partner="Cilvēks, kuru vēlies uzaicināt")
async def pair_invite(interaction: discord.Interaction,
                      partner: discord.Member):
    if partner.bot or partner.id == interaction.user.id:
        await interaction.response.send_message(
            "Izvēlies citu cilvēku, nevis botu vai sevi.",
            ephemeral=True
        )
        return

    if get_pair_for_user(interaction.user.id)[0] or \
       get_pair_for_user(partner.id)[0]:
        await interaction.response.send_message(
            "Viens no jums jau ir savienots pārī.",
            ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"{partner.mention}, {interaction.user.mention} "
        "aicina tevi izveidot pāra telpu. ❤️",
        view=PairInvite(interaction.user, partner)
    )

@bot.tree.command(
    name="task",
    description="Parādi šodienas pāra uzdevumu"
)
async def task(interaction: discord.Interaction):
    pair_id, pair = get_pair_for_user(interaction.user.id)
    if not pair:
        await interaction.response.send_message(
            "Vispirms izveido pāri ar `/pair_invite`.",
            ephemeral=True
        )
        return

    if interaction.guild_id != pair["guild_id"]:
        await interaction.response.send_message(
            "Izmanto šo komandu savā Discord serverī.",
            ephemeral=True
        )
        return

    today = date.today().isoformat()
    if pair["task_date"] != today:
        previous = {
            "date": pair["task_date"],
            "task": pair["task_text"],
            "answers": pair["answers"].copy()
        }
        if pair["task_text"]:
            pair["history"].append(previous)

        choices = [t for t in TASKS if t != pair["task_text"]]
        pair["task_text"] = random.choice(choices or TASKS)
        pair["task_date"] = today
        pair["answers"] = {}
        save_data()

    channel = interaction.guild.get_channel(pair["tasks_channel_id"])
    if channel is None:
        await interaction.response.send_message(
            "Uzdevumu kanāls nav atrasts. Pārbaudi kanāla iestatījumus.",
            ephemeral=True
        )
        return

    await channel.send(
        f"📅 **Dienas uzdevums — {today}**\n\n"
        f"{pair['task_text']}\n\n"
        "Katrs iesniedz savu atbildi ar `/answer`."
    )
    await interaction.response.send_message(
        "Dienas uzdevums publicēts privātajā kanālā.",
        ephemeral=True
    )

@bot.tree.command(
    name="answer",
    description="Iesniedz savu atbildi dienas uzdevumam"
)
@app_commands.describe(teksts="Tava atbilde uz šodienas uzdevumu")
async def answer(interaction: discord.Interaction, teksts: str):
    pair_id, pair = get_pair_for_user(interaction.user.id)
    if not pair:
        await interaction.response.send_message(
            "Tev vēl nav izveidots pāris.",
            ephemeral=True
        )
        return

    if pair["task_date"] != date.today().isoformat():
        await interaction.response.send_message(
            "Vispirms palūdz dienas uzdevumu ar `/task`.",
            ephemeral=True
        )
        return

    pair["answers"][str(interaction.user.id)] = teksts
    save_data()

    history_channel = interaction.guild.get_channel(
        pair["history_channel_id"]
    ) if interaction.guild else None

    if history_channel:
        await history_channel.send(
            f"✍️ **Atbilde no {interaction.user.display_name}**\n"
            f"{teksts}"
        )
