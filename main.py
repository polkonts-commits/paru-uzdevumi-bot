
import json
import os
import random
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
DATA_FILE = Path(os.getenv("DATA_FILE", "data.json"))
LATVIA_TZ = ZoneInfo("Europe/Riga")

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
    "Atcerieties, kāds bija jūsu pirmais iespaids vienam par otru.",
]


def load_data():
    if not DATA_FILE.exists():
        return {"pairs": {}}
    try:
        loaded = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        if not isinstance(loaded, dict) or not isinstance(loaded.get("pairs"), dict):
            raise ValueError("Nederīga datu faila struktūra")
        return loaded
    except (json.JSONDecodeError, OSError, ValueError) as error:
        print(f"Neizdevās ielādēt {DATA_FILE}: {error}")
        return {"pairs": {}}


data = load_data()


def save_data():
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, ensure_ascii=False, indent=2)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=DATA_FILE.parent, delete=False
        ) as temp_file:
            temp_file.write(content)
            temp_path = Path(temp_file.name)
        temp_path.replace(DATA_FILE)
    finally:
        if temp_path and temp_path.exists():
            temp_path.unlink(missing_ok=True)


def today_string():
    return datetime.now(LATVIA_TZ).date().isoformat()


def get_pair_for_user(user_id):
    target_id = int(user_id)
    for pair_id, pair in data["pairs"].items():
        members = {int(member_id) for member_id in pair.get("members", [])}
        if target_id in members:
            return pair_id, pair
    return None, None


async def fetch_guild_channel(guild, channel_id):
    if guild is None or channel_id is None:
        return None
    channel = guild.get_channel(int(channel_id))
    if channel is not None:
        return channel
    try:
        return await guild.fetch_channel(int(channel_id))
    except (discord.NotFound, discord.Forbidden, discord.HTTPException):
        return None


def user_is_in_guild_pair(interaction, pair):
    return (
        interaction.guild_id is not None
        and int(interaction.guild_id) == int(pair.get("guild_id", 0))
        and int(interaction.user.id) in {
            int(member_id) for member_id in pair.get("members", [])
        }
    )


intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


class PairInvite(discord.ui.View):
    def __init__(self, inviter, invitee):
        super().__init__(timeout=86400)
        self.inviter = inviter
        self.invitee = invitee

    @discord.ui.button(
        label="Pieņemt uzaicinājumu",
        style=discord.ButtonStyle.success,
        emoji="❤️",
    )
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.invitee.id:
            await interaction.response.send_message(
                "Šis uzaicinājums ir paredzēts citam cilvēkam.", ephemeral=True
            )
            return
        if interaction.guild is None:
            await interaction.response.send_message(
                "Šo darbību var veikt tikai Discord serverī.", ephemeral=True
            )
            return
        if get_pair_for_user(self.inviter.id)[0] or get_pair_for_user(self.invitee.id)[0]:
            await interaction.response.send_message(
                "Viens no jums jau ir savienots pārī.", ephemeral=True
            )
            return

        bot_member = interaction.guild.me
        if bot_member is None or not bot_member.guild_permissions.manage_channels:
            await interaction.response.send_message(
                "Botam vajadzīga Manage Channels atļauja, lai izveidotu privāto pāra telpu.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        category = None
        created_channels = []
        try:
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(
                    view_channel=False
                ),
                self.inviter: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                ),
                self.invitee: discord.PermissionOverwrite(
                    view_channel=True, send_messages=True, read_message_history=True
                ),
                bot_member: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True,
                ),
            }
            category = await interaction.guild.create_category(
                f"💞 {self.inviter.display_name} + {self.invitee.display_name}",
                overwrites=overwrites,
                reason="Privātas pāra telpas izveide",
            )
            tasks_channel = await interaction.guild.create_text_channel(
                "💞-dienas-uzdevumi", category=category,
                reason="Pāra dienas uzdevumu kanāls",
            )
            created_channels.append(tasks_channel)
            history_channel = await interaction.guild.create_text_channel(
                "📚-uzdevumu-vesture", category=category,
                reason="Pāra uzdevumu vēstures kanāls",
            )
            created_channels.append(history_channel)

            pair_id = str(category.id)
            data["pairs"][pair_id] = {
                "guild_id": interaction.guild.id,
                "members": [self.inviter.id, self.invitee.id],
                "category_id": category.id,
                "tasks_channel_id": tasks_channel.id,
                "history_channel_id": history_channel.id,
                "task_date": "",
                "task_text": "",
                "answers": {},
                "history": [],
            }
            save_data()
            await tasks_channel.send(
                f"Sveicināti, {self.inviter.mention} un {self.invitee.mention}! ❤️\n"
                "Jūsu privātā pāra telpa ir gatava.\n\n"
                "Komandas:\n"
                "• /task — publicē šodienas uzdevumu\n"
                "• /answer — iesniedz savu atbildi\n"
                "• /unpair — noņem pāri pēc apstiprinājuma"
            )
            await history_channel.send(
                "📚 Šeit glabāsies iepriekšējo uzdevumu un atbilžu vēsture."
            )
            await interaction.followup.send(
                "Uzaicinājums pieņemts! Jūsu privātā telpa ir izveidota.",
                ephemeral=True,
            )
            self.stop()
        except (discord.HTTPException, OSError) as error:
            if category is not None:
                data["pairs"].pop(str(category.id), None)
            try:
                save_data()
            except OSError:
                pass
            for channel in reversed(created_channels):
                try:
                    await channel.delete(reason="Neizdevās pabeigt pāra telpas izveidi")
                except discord.HTTPException:
                    pass
            if category is not None:
                try:
                    await category.delete(reason="Neizdevās pabeigt pāra telpas izveidi")
                except discord.HTTPException:
                    pass
            print(f"Pāra telpas izveides kļūda: {error}")
            await interaction.followup.send(
                "Neizdevās pilnībā izveidot pāra telpu. Pārbaudi bota atļaujas un mēģini vēlreiz.",
                ephemeral=True,
            )


class UnpairConfirmation(discord.ui.View):
    def __init__(self, pair_id, requester_id):
        super().__init__(timeout=60)
        self.pair_id = pair_id
        self.requester_id = requester_id

    @discord.ui.button(label="Jā, noņemt pāri", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message(
                "Šo apstiprinājumu var izmantot tikai tā persona, kura sāka darbību.",
                ephemeral=True,
            )
            return
        pair = data["pairs"].get(self.pair_id)
        if not pair or not user_is_in_guild_pair(interaction, pair):
            await interaction.response.send_message(
                "Pāris nav atrasts vai šī darbība nav atļauta šajā serverī.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        try:
            for channel_id in (
                pair.get("tasks_channel_id"),
                pair.get("history_channel_id"),
            ):
                channel = await fetch_guild_channel(guild, channel_id)
                if channel is not None:
                    await channel.delete(reason="Pāris noņemts ar /unpair")
            category = await fetch_guild_channel(guild, pair.get("category_id"))
            if category is not None:
                await category.delete(reason="Pāris noņemts ar /unpair")
            data["pairs"].pop(self.pair_id, None)
            save_data()
            await interaction.followup.send(
                "Pāris noņemts. Tā privātie kanāli un saglabātā bota vēsture ir dzēsti.",
                ephemeral=True,
            )
            self.stop()
        except (discord.HTTPException, OSError) as error:
            print(f"Pāra noņemšanas kļūda: {error}")
            await interaction.followup.send(
                "Pāri neizdevās pilnībā noņemt. Pārbaudi bota Manage Channels atļauju; saglabātie dati nav apzināti dzēsti.",
                ephemeral=True,
            )

    @discord.ui.button(label="Atcelt", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.requester_id:
            await interaction.response.send_message(
                "Šo apstiprinājumu var izmantot tikai tā persona, kura sāka darbību.",
                ephemeral=True,
            )
            return
        await interaction.response.edit_message(
            content="Pāra noņemšana atcelta.", view=None
        )
        self.stop()


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"Bot: {bot.user} | Sinhronizētas {len(synced)} komandas")
    except discord.HTTPException as error:
        print(f"Komandu sinhronizācijas kļūda: {error}")


@bot.tree.command(
    name="pair_invite",
    description="Uzaicini partneri izveidot privātu pāra telpu",
)
@app_commands.describe(partner="Cilvēks, kuru vēlies uzaicināt")
async def pair_invite(interaction: discord.Interaction, partner: discord.Member):
    if partner.bot or partner.id == interaction.user.id:
        await interaction.response.send_message(
            "Izvēlies citu cilvēku, nevis botu vai sevi.", ephemeral=True
        )
        return
    if interaction.guild is None:
        await interaction.response.send_message(
            "Šo komandu var izmantot tikai Discord serverī.", ephemeral=True
        )
        return
    if get_pair_for_user(interaction.user.id)[0] or get_pair_for_user(partner.id)[0]:
        await interaction.response.send_message(
            "Viens no jums jau ir savienots pārī. Vispirms izmantojiet /unpair.",
            ephemeral=True,
        )
        return
    await interaction.response.send_message(
        f"{partner.mention}, {interaction.user.mention} aicina tevi izveidot pāra telpu. ❤️",
        view=PairInvite(interaction.user, partner),
        allowed_mentions=discord.AllowedMentions(users=True),
    )


@bot.tree.command(
    name="task",
    description="Publicē šodienas pāra uzdevumu",
)
async def task(interaction: discord.Interaction):
    _, pair = get_pair_for_user(interaction.user.id)
    if not pair:
        await interaction.response.send_message(
            "Vispirms izveido pāri ar /pair_invite.", ephemeral=True
        )
        return
    if not user_is_in_guild_pair(interaction, pair):
        await interaction.response.send_message(
            "Izmanto šo komandu savā pāra Discord serverī.", ephemeral=True
        )
        return

    today = today_string()
    is_new_task = pair.get("task_date") != today
    if is_new_task:
        previous = {
            "date": pair.get("task_date", ""),
            "task": pair.get("task_text", ""),
            "answers": dict(pair.get("answers", {})),
        }
        if pair.get("task_text"):
            pair.setdefault("history", []).append(previous)
        choices = [item for item in TASKS if item != pair.get("task_text")]
        pair["task_text"] = random.choice(choices or TASKS)
        pair["task_date"] = today
        pair["answers"] = {}
        try:
            save_data()
        except OSError as error:
            print(f"Neizdevās saglabāt dienas uzdevumu: {error}")
            await interaction.response.send_message(
                "Neizdevās saglabāt uzdevumu. Pārbaudi, vai botam ir tiesības rakstīt datu failā.",
                ephemeral=True,
            )
            return

    channel = await fetch_guild_channel(
        interaction.guild, pair.get("tasks_channel_id")
    )
    if channel is None or not hasattr(channel, "send"):
        await interaction.response.send_message(
            "Uzdevumu kanāls nav atrasts. Pārbaudi bota kanālu atļaujas.",
            ephemeral=True,
        )
        return
    if is_new_task:
        await channel.send(
            f"📅 **Dienas uzdevums — {today}**\n\n"
            f"{pair['task_text']}\n\n"
            "Katrs iesniedz savu atbildi ar /answer."
        )
        await interaction.response.send_message(
            "Šodienas uzdevums publicēts privātajā kanālā.", ephemeral=True
        )
    else:
        await interaction.response.send_message(
            f"Šodienas uzdevums jau ir publicēts:\n\n**{pair['task_text']}**",
            ephemeral=True,
        )


@bot.tree.command(
    name="answer",
    description="Iesniedz savu atbildi dienas uzdevumam",
)
@app_commands.describe(teksts="Tava atbilde uz šodienas uzdevumu")
async def answer(
    interaction: discord.Interaction,
    teksts: app_commands.Range[str, 1, 1000],
):
    _, pair = get_pair_for_user(interaction.user.id)
    if not pair:
        await interaction.response.send_message(
            "Tev vēl nav izveidots pāris.", ephemeral=True
        )
        return
    if not user_is_in_guild_pair(interaction, pair):
        await interaction.response.send_message(
            "Izmanto šo komandu savā pāra Discord serverī.", ephemeral=True
        )
        return
    if pair.get("task_date") != today_string() or not pair.get("task_text"):
        await interaction.response.send_message(
            "Vispirms palūdz dienas uzdevumu ar /task.", ephemeral=True
        )
        return

    pair.setdefault("answers", {})[str(interaction.user.id)] = str(teksts)
    try:
        save_data()
    except OSError as error:
        print(f"Neizdevās saglabāt atbildi: {error}")
        await interaction.response.send_message(
            "Neizdevās saglabāt atbildi. Mēģini vēlreiz pēc brīža.",
            ephemeral=True,
        )
        return

    history_channel = await fetch_guild_channel(
        interaction.guild, pair.get("history_channel_id")
    )
    if history_channel is not None and hasattr(history_channel, "send"):
        try:
            await history_channel.send(
                f"✍️ **Atbilde no {interaction.user.display_name}**\n{teksts}"
            )
        except discord.HTTPException as error:
            print(f"Neizdevās publicēt atbildi vēstures kanālā: {error}")

    submitted_count = len(pair["answers"])
    await interaction.response.send_message(
        f"Atbilde saglabāta. Iesniegtas {submitted_count}/2 atbildes šodienas uzdevumam.",
        ephemeral=True,
    )


@bot.tree.command(
    name="unpair",
    description="Noņem pāri un tā privātos kanālus",
)
async def unpair(interaction: discord.Interaction):
    pair_id, pair = get_pair_for_user(interaction.user.id)
    if not pair:
        await interaction.response.send_message(
            "Tev nav aktīva pāra, ko noņemt.", ephemeral=True
        )
        return
    if not user_is_in_guild_pair(interaction, pair):
        await interaction.response.send_message(
            "Šo pāri vari noņemt tikai tā Discord serverī.", ephemeral=True
        )
        return
    await interaction.response.send_message(
        "Vai tiešām noņemt pāri? Tiks dzēsti abi privātie kanāli, kategorija un bota saglabātā uzdevumu/atbilžu vēsture.",
        view=UnpairConfirmation(pair_id, interaction.user.id),
        ephemeral=True,
    )


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit(
            "Trūkst DISCORD_TOKEN vides mainīgā. Iestati Discord bota tokenu un palaid programmu vēlreiz."
        )
    bot.run(TOKEN)
