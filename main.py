
import json
import os
import random
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import commands, tasks

TOKEN = os.getenv("DISCORD_TOKEN")
DATA_FILE = Path(os.getenv("DATA_FILE", "data.json"))
LATVIA_TZ = ZoneInfo("Europe/Riga")

TASKS = {
    "kopā": [
        ("Romantika", "Apskaujiet viens otru vismaz divdesmit sekundes, nesteidzoties."),
        ("Romantika", "Katrs pasakiet trīs lietas, ko šodien novērtējat otrā."),
        ("Romantika", "Atcerieties savu pirmo iespaidu vienam par otru un izstāstiet to vēlreiz."),
        ("Romantika", "Katrs pasakiet vienu kopīgu atmiņu, kuru gribētos piedzīvot vēlreiz."),
        ("Romantika", "Sarīkojiet viens otram piecu minūšu masāžu, ja abiem tas ir patīkami."),
        ("Romantika", "Noskūpstiet viens otru un pasakiet, kas jums šobrīd patīk jūsu attiecībās."),
        ("Iepazīšanās", "Uzdodiet viens otram jautājumu, kuru sen gribējāt uzdot."),
        ("Iepazīšanās", "Katrs nosauciet vienu vēlmi, ko gribētu kopā īstenot šajā mēnesī."),
        ("Iepazīšanās", "Pastāstiet, kas jums palīdz justies mīlētiem un novērtētiem."),
        ("Izaicinājums", "Izvēlieties dziesmu, kas raksturo jūsu attiecības, un paskaidrojiet izvēli."),
        ("Izaicinājums", "Izdomājiet spontānu randiņu, ko varat sarīkot tuvāko septiņu dienu laikā."),
        ("Humors", "Katrs atdariniet otru desmit sekundes — draudzīgi un bez aizvainojuma."),
        ("18+", "Ja abi vēlaties, vienojieties par kādu jaunu skūpstu vai pieskārienu, ko izmēģināt."),
        ("18+", "Katrs nosauciet vienu lietu, kas jums šķiet pievilcīga otrā."),
        ("18+", "Ja abiem ir ērti, nosūtiet viens otram privātu pikantu foto. Pirms fotografēšanas vienojieties par robežām; uzdevumu drīkst izlaist."),
        ("18+", "Izrunājiet vienu intīmu vēlmi, ko abi labprāt apspriestu bez spiediena."),
        ("18+", "Ja abi piekrītat, uzņemiet privātu, juteklisku video tikai viens otram. Neievietojiet to publiski; jebkurš var atteikties."),
        ("18+", "Sarunājiet viens otram romantisku vai juteklisku pārsteigumu, kas abiem ir patīkams."),
    ],
    "attālināti": [
        ("Romantika", "Nosūtiet viens otram balss ziņu ar patiesu komplimentu."),
        ("Romantika", "Sarīkojiet desmit minūšu videozvanu, kurā runājat tikai par patīkamām lietām."),
        ("Romantika", "Nosūtiet foto ar kaut ko, kas šodien lika jums atcerēties partneri."),
        ("Iepazīšanās", "Katrs pastāstiet vienu lietu par savu dienu, ko otrs vēl nezina."),
        ("Iepazīšanās", "Uzdodiet viens otram jautājumu un atbildiet godīgi."),
        ("Izaicinājums", "Nosūtiet viens otram dziesmu, kas atbilst jūsu šībrīža noskaņojumam."),
        ("Izaicinājums", "Vienlaikus noskatieties vienu īsu video un pēc tam apmainieties ar iespaidiem."),
        ("Humors", "Nosūtiet smieklīgu pašbildi vai emocijzīmi, kas raksturo jūsu dienu."),
        ("Humors", "Katrs nosūtiet trīs emocijzīmes, kas raksturo otru, un paskaidrojiet izvēli."),
        ("18+", "Ja abi vēlaties, nosūtiet partnerim privātu pikantu foto. Vispirms vienojieties par robežām; uzdevumu drīkst izlaist."),
        ("18+", "Veiciet privātu videozvanu un katrs nosauciet vienu romantisku vai juteklisku vēlmi, ko gribētu apspriest."),
        ("18+", "Ja abi skaidri piekrītat, nosūtiet partnerim privātu juteklisku video. Neviens nav spiests to darīt, un saturu nevajag pārsūtīt tālāk."),
        ("18+", "Nosūtiet partnerim flirtējošu ziņu, kas liek viņam pasmaidīt."),
        ("18+", "Pastāstiet viens otram, kāds randiņš jums šķistu īpaši romantisks vai juteklisks."),
    ],
}

MODE_LABELS = {
    "kopā": "🫂 Uzdevums kopā",
    "attālināti": "📱 Uzdevums attālināti",
    "random": "🎲 Nejauši — visi uzdevumi",
}


# Papildu uzdevumi — tos pievieno esošajai bibliotēkai, saglabājot režīmus.
TASKS["kopā"].extend([
    ("Romantika", "Katrs nosauciet vienu mazu ikdienas lietu, ko otrs dara un kas jums ir svarīga."),
    ("Romantika", "Turiet viens otra rokas un minūti runājiet par kaut ko, ko gaidāt nākotnē."),
    ("Romantika", "Izvēlieties kopīgu fotogrāfiju un pastāstiet, kāpēc tā jums ir īpaša."),
    ("Romantika", "Katrs nosauciet vienu veidu, kā partneris varētu jums palīdzēt grūtā dienā."),
    ("Romantika", "Sarīkojiet piecu minūšu randiņu bez telefoniem."),
    ("Romantika", "Katrs pasakiet vienu komplimentu par otra raksturu, nevis izskatu."),
    ("Romantika", "Izvēlieties vienu kopīgu tradīciju, ko gribētu ieviest."),
    ("Romantika", "Katrs pabeidziet teikumu: “Es jūtos tev vistuvāk, kad…”"),
    ("Iepazīšanās", "Pastāstiet par bērnības atmiņu, kuru partneris vēl nav dzirdējis."),
    ("Iepazīšanās", "Katrs nosauciet vienu prasmi, ko gribētu iemācīties kopā."),
    ("Iepazīšanās", "Kas ir viena lieta, ko cilvēki par jums bieži pārprot? Izstāstiet partnerim."),
    ("Iepazīšanās", "Katrs nosauciet trīs lietas, kas palīdz jums atpūsties."),
    ("Iepazīšanās", "Izrunājiet vienu sapni, kuru vēl neesat īstenojuši."),
    ("Iepazīšanās", "Katrs nosauciet vienu vērtību, kas jums attiecībās ir vissvarīgākā."),
    ("Izaicinājums", "Pagatavojiet vai izvēlieties viens otram nelielu uzkodu."),
    ("Izaicinājums", "Izvēlieties filmu vai seriālu nākamajam kopīgajam vakaram."),
    ("Izaicinājums", "Izdomājiet trīs lētus randiņus, ko varētu izmēģināt."),
    ("Izaicinājums", "Katrs izdomājiet vienu jautru aktivitāti, ko darīt nākamajā brīvajā dienā."),
    ("Izaicinājums", "Uztaisiet kopīgu selfiju, ja abiem tas ir patīkami."),
    ("Humors", "Katrs izdomājiet partnerim mīļu iesauku un paskaidrojiet, kāpēc."),
    ("Humors", "Izspēlējiet akmens–šķēres–papīrītis trīs kārtas; uzvarētājs izvēlas nākamo kopīgo dziesmu."),
    ("Humors", "Katrs pasakiet vienu smieklīgu lietu, ko darāt, kad neviens neskatās."),
    ("Humors", "Izdomājiet jūsu attiecībām filmas nosaukumu."),
    ("18+", "Ja abiem ir vēlme, vienojieties par skūpstu vai pieskārienu, kas abiem patīk."),
    ("18+", "Katrs nosauciet vienu lietu, kas jums palīdz justies iekārotiem un drošībā."),
    ("18+", "Izrunājiet, kas jums abiem ir patīkami flirtā un kādas ir jūsu robežas."),
    ("18+", "Ja abi piekrītat, uzrakstiet viens otram pikantu, bet ne pārāk atklātu ziņu."),
    ("18+", "Katrs nosauciet vienu romantisku fantāziju, ko labprāt apspriestu; nav pienākuma to īstenot."),
    ("18+", "Vienojieties par drošu vārdu vai signālu, ar kuru jebkurš var apturēt intīmu izaicinājumu."),
    ("18+", "Ja abi vēlaties, izvēlieties privātu foto izaicinājumu un pirms tam vienojieties, ko ir ērti sūtīt."),
    ("18+", "Sarunājiet intīmu randiņu, kurā abi varat jebkurā brīdī pateikt “nē” vai mainīt plānu."),
])

TASKS["attālināti"].extend([
    ("Romantika", "Nosūtiet viens otram balss ziņu, kurā pasakāt, ko šodien novērtējat partnerī."),
    ("Romantika", "Sarīkojiet virtuālu kafijas vai tējas pauzi videozvanā."),
    ("Romantika", "Nosūtiet foto ar skatu no vietas, kur pašlaik atrodaties."),
    ("Romantika", "Katrs uzrakstiet vienu teikumu par to, ko gribētu darīt, kad atkal būsiet kopā."),
    ("Romantika", "Izvēlieties vienu dziesmu un noklausieties to vienlaikus."),
    ("Romantika", "Nosūtiet partnerim trīs iemeslus, kāpēc šodien par viņu domājāt."),
    ("Iepazīšanās", "Katrs pastāstiet par vienu šīs dienas notikumu, kas jūs pārsteidza."),
    ("Iepazīšanās", "Uzdodiet jautājumu par partnera sapni vai mērķi un noklausieties atbildi."),
    ("Iepazīšanās", "Nosūtiet viens otram bērnības vai skolas laika atmiņu."),
    ("Iepazīšanās", "Katrs pasakiet, kas jums palīdz justies tuviem arī tad, kad esat tālu."),
    ("Izaicinājums", "Vienlaikus pagatavojiet vienu un to pašu dzērienu un sazvanieties."),
    ("Izaicinājums", "Izvēlieties vienu mazu mērķi, ko abi paveiksiet līdz rītdienai."),
    ("Izaicinājums", "Nosūtiet foto ar priekšmetu, kas jums atgādina par otru."),
    ("Izaicinājums", "Sarīkojiet piecu minūšu videozvanu bez citu lietu darīšanas paralēli."),
    ("Izaicinājums", "Katrs iesakiet otram vienu dziesmu, filmu vai grāmatu."),
    ("Humors", "Nosūtiet pašreizējās sejas izteiksmi, kas raksturo jūsu garastāvokli."),
    ("Humors", "Izdomājiet trīs smieklīgus vārdus, kas raksturo jūsu pāri."),
    ("Humors", "Nosūtiet viens otram mēmi, kas vislabāk raksturo jūsu attiecības."),
    ("Humors", "Katrs uzrakstiet īsu ziņu tā, it kā jūs būtu ziņu diktori."),
    ("18+", "Ja abi vēlaties, nosūtiet privātu flirtējošu ziņu un ļaujiet partnerim atbildēt savā tempā."),
    ("18+", "Sarunājiet privātu videozvanu un pastāstiet, kas jums šķiet pievilcīgs otrā."),
    ("18+", "Ja abiem ir ērti, nosūtiet privātu pikantu foto; vispirms vienojieties par robežām."),
    ("18+", "Katrs nosauciet vienu intīmu vēlmi, ko gribētu mierīgi pārrunāt."),
    ("18+", "Ja abi skaidri piekrītat, nosūtiet viens otram privātu juteklisku video. Uzdevumu var izlaist, un saturu nedrīkst pārsūtīt bez atļaujas."),
    ("18+", "Nosūtiet partnerim balss ziņu ar flirtējošu komplimentu."),
    ("18+", "Izrunājiet, kādas fotogrāfijas vai ziņas jums abiem ir patīkami saņemt un ko nevēlaties saņemt."),
    ("18+", "Izvēlieties attālinātu randiņu ar romantisku vai juteklisku noskaņu, kas abiem ir ērta."),
])


# Jauns uzdevumu papildinājums — dažādībai un mazāk atkārtojumiem.
TASKS["kopā"].extend([
    ("Komunikācija", "Katrs pabeidziet teikumu: “Man ir vieglāk tev pastāstīt par grūtībām, kad…”"),
    ("Komunikācija", "Vienojieties par vienu frāzi, ko lietot, kad vajadzīga pauze strīda laikā."),
    ("Komunikācija", "Katrs nosauciet vienu lietu, ko partneris var darīt, lai jūs labāk uzklausītu."),
    ("Komunikācija", "Piecas minūtes runājiet pārmaiņus: viens runā, otrs tikai klausās, pēc tam mainieties."),
    ("Komunikācija", "Katrs pasakiet vienu pateicību par kaut ko pavisam ikdienišķu."),
    ("Kopīga nākotne", "Izveidojiet sarakstu ar trim lietām, ko gribētu piedzīvot nākamajā gadā."),
    ("Kopīga nākotne", "Izvēlieties vienu kopīgu mērķi un nosauciet pirmo mazo soli tā sasniegšanai."),
    ("Kopīga nākotne", "Iedomājieties ideālu brīvdienu kopā un salīdziniet savas idejas."),
    ("Kopīga nākotne", "Katrs nosauciet vienu jaunu tradīciju, ko varētu ieviest katru mēnesi."),
    ("Atmiņas", "Pastāstiet par brīdi, kad partneris jūs patīkami pārsteidza."),
    ("Atmiņas", "Atrodiet kopīgu atmiņu, par kuru parasti nerunājat, un izstāstiet, ko tā jums nozīmē."),
    ("Atmiņas", "Katrs nosauciet vienu vietu, uz kuru gribētu aizbraukt kopā, un kāpēc."),
    ("Ikdiena", "Izvēlieties vienu mazu pienākumu, ko šonedēļ varētu atvieglot otram."),
    ("Ikdiena", "Katrs pasakiet, kas jums palīdz atgūt spēkus pēc smagas dienas."),
    ("Ikdiena", "Sarīkojiet desmit minūšu kārtības vai plānošanas sprintu, lai atbrīvotu laiku kopā būšanai."),
    ("Spēle", "Izdomājiet viens otram trīs jautājumus ar atbilžu variantiem un pārbaudiet, cik labi pazīstat viens otru."),
    ("Spēle", "Katrs uzzīmējiet otru trīsdesmit sekundēs un parādiet rezultātu."),
    ("Spēle", "Izvēlieties nejaušu priekšmetu tuvumā un izdomājiet tam smieklīgu kopīgu pielietojumu."),
    ("Spēle", "Spēlējiet “divas patiesības un viens izdomājums” par savu dzīvi."),
    ("Tuvība", "Katrs nosauciet vienu robežu un vienu lietu, kas palīdz justies droši attiecībās."),
    ("Tuvība", "Pajautājiet partnerim, kāds uzmanības apliecinājums viņam šonedēļ būtu vispatīkamākais."),
    ("Tuvība", "Ja abiem patīkami, pasēdiet apskāvušies klusumā vienu minūti."),
    ("18+", "Privāti pārrunājiet, kāda veida flirtu katrs šobrīd vēlas un kāda veida ne."),
    ("18+", "Katrs nosauciet vienu romantisku pieskārienu, kas jums patīk; nekas nav jāizmēģina bez abu piekrišanas."),
    ("18+", "Izveidojiet kopīgu “jā / varbūt / nē” sarakstu romantiskām vai intīmām idejām un pārrunājiet to bez spiediena."),
    ("18+", "Sarunājiet vakaru ar romantisku noskaņu, kurā jebkurš var mainīt domas vai pārtraukt aktivitāti."),
])

TASKS["attālināti"].extend([
    ("Komunikācija", "Nosūtiet partnerim ziņu: “Šodien es gribētu, lai tu zini…” un pabeidziet to godīgi."),
    ("Komunikācija", "Sazvanieties uz piecām minūtēm un katrs atkārtojiet vienu svarīgu domu, ko dzirdējāt no otra."),
    ("Komunikācija", "Katrs nosūtiet vienu jautājumu, kas palīdzētu labāk saprast otra pašreizējo noskaņojumu."),
    ("Komunikācija", "Vienojieties par vienu veidu, kā paziņot, ka esat aizņemts, bet vēlāk gribat sazināties."),
    ("Kopīga nākotne", "Katrs nosūtiet vienu ideju nākamajam randiņam un kopā izvēlieties vienu."),
    ("Kopīga nākotne", "Izveidojiet kopīgu trīs lietu sarakstu, ko gribat paveikt nākamajā mēnesī."),
    ("Kopīga nākotne", "Atrodiet vietu kartē, ko gribētu apmeklēt kopā, un nosūtiet viens otram saiti."),
    ("Atmiņas", "Nosūtiet vienu vecu foto vai aprakstiet atmiņu, kas jums liek pasmaidīt."),
    ("Atmiņas", "Katrs pastāstiet par brīdi, kad jutāties īpaši atbalstīti no partnera."),
    ("Atmiņas", "Nosūtiet dziesmu, kas atgādina par konkrētu kopīgu notikumu, un paskaidrojiet kāpēc."),
    ("Ikdiena", "Nosūtiet foto ar savu šodienas mazo uzvaru."),
    ("Ikdiena", "Katrs izvēlieties vienu mazu pašaprūpes darbību un vakarā pastāstiet, kā izdevās."),
    ("Ikdiena", "Sarīkojiet vienlaicīgu tējas vai kafijas pauzi un apmainieties ar vienu labu ziņu."),
    ("Spēle", "Spēlējiet attālināti “uzmini priekšmetu”: aprakstiet kaut ko sev blakus, nenosaucot tā vārdu."),
    ("Spēle", "Katrs nosūtiet trīs faktus par savu dienu, un partnerim jāuzmin, kurš ir svarīgākais."),
    ("Spēle", "Izveidojiet viens otram īsu viktorīnu par kopīgām atmiņām."),
    ("Spēle", "Nosūtiet piecu sekunžu audio ar kādu skaņu un ļaujiet otram uzminēt, kas tas ir."),
    ("Tuvība", "Pajautājiet partnerim, vai viņam šodien vairāk vajadzīgs padoms, uzklausīšana vai uzmundrinājums."),
    ("Tuvība", "Nosūtiet vienu konkrētu komplimentu par partnera rīcību vai rakstura īpašību."),
    ("Tuvība", "Katrs pabeidziet ziņā teikumu: “Es jūtos tev tuvu, kad tu…”"),
    ("18+", "Pirms flirtējošas vai pikantas ziņas nosūtīšanas pajautājiet, vai partnerim šobrīd tāds saturs ir vēlams."),
    ("18+", "Katrs nosauciet vienu romantisku ideju nākamajam randiņam, kuru abi varat brīvi pieņemt vai noraidīt."),
    ("18+", "Pārrunājiet, kā saglabāt privātumu, ja sūtāt viens otram personiskas ziņas vai attēlus."),
    ("18+", "Nosūtiet partnerim flirtējošu komplimentu bez prasības uzreiz atbildēt."),
    ("18+", "Kopīgi izveidojiet “jā / varbūt / nē” sarakstu intīmām idejām, katram atbildot tikai tik detalizēti, cik ērti."),
])


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
                "task_category": "",
                "task_mode": "random",
                "task_completed": False,
                "completed_tasks": 0,
                "streak": 0,
                "last_completed_date": "",
                "answers": {},
                "history": [],
            }
            save_data()
            await tasks_channel.send(
                f"Sveicināti, {self.inviter.mention} un {self.invitee.mention}! ❤️\n"
                "Jūsu privātā pāra telpa ir gatava.\n\n"
                "Komandas:\n"
                "• /task — publicē šodienas uzdevumu\n"
                "• /task_mode — izvēlies kopā, attālināti vai nejauši\n"
                "• /answer — iesniedz savu atbildi\n"
                "• /stats — apskati izpildītos uzdevumus un dienu sēriju\n"
                "• /unpair — noņem pāri pēc apstiprinājuma",
                view=TaskModeView()
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


class TaskModeView(discord.ui.View):
    """Persistent mode selector posted in each couple's private task channel."""

    def __init__(self):
        super().__init__(timeout=None)

    async def set_mode(self, interaction: discord.Interaction, mode: str):
        _, pair = get_pair_for_user(interaction.user.id)
        if not pair or not user_is_in_guild_pair(interaction, pair):
            await interaction.response.send_message(
                "Šo izvēli var veikt tikai sava pāra privātajā serverī.",
                ephemeral=True,
            )
            return
        if interaction.channel_id != int(pair.get("tasks_channel_id", 0)):
            await interaction.response.send_message(
                "Režīmu vari mainīt sava pāra uzdevumu kanālā.",
                ephemeral=True,
            )
            return
        pair["task_mode"] = mode
        try:
            save_data()
        except OSError as error:
            print(f"Neizdevās saglabāt uzdevumu režīmu: {error}")
            await interaction.response.send_message(
                "Neizdevās saglabāt izvēli. Mēģini vēlreiz.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            f"Uzdevumu režīms nomainīts: **{MODE_LABELS[mode]}**. "
            "Izvēle paliks spēkā, līdz to nomainīsiet.",
            ephemeral=True,
        )

    @discord.ui.button(
        label="Kopā", emoji="🫂", style=discord.ButtonStyle.success,
        custom_id="task_mode:together",
    )
    async def together(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_mode(interaction, "kopā")

    @discord.ui.button(
        label="Attālināti", emoji="📱", style=discord.ButtonStyle.primary,
        custom_id="task_mode:remote",
    )
    async def remote(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_mode(interaction, "attālināti")

    @discord.ui.button(
        label="Nejauši — visi", emoji="🎲", style=discord.ButtonStyle.secondary,
        custom_id="task_mode:random",
    )
    async def random_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.set_mode(interaction, "random")


async def publish_automatic_daily_tasks():
    """Publicē katra pāra dienas uzdevumu no plkst. 09.00 pēc Latvijas laika."""
    now = datetime.now(LATVIA_TZ)
    if now.hour < 9:
        return

    today = now.date().isoformat()
    for pair_id, pair in list(data.get("pairs", {}).items()):
        if pair.get("task_date") == today:
            continue

        guild = bot.get_guild(int(pair.get("guild_id", 0)))
        if guild is None:
            continue
        channel = await fetch_guild_channel(guild, pair.get("tasks_channel_id"))
        if channel is None or not hasattr(channel, "send"):
            continue

        mode = pair.get("task_mode", "random")
        if mode not in TASKS and mode != "random":
            mode = "random"
            pair["task_mode"] = mode
        if mode == "random":
            available = [
                (category, task_text)
                for group in TASKS.values()
                for category, task_text in group
            ]
        else:
            available = list(TASKS[mode])

        used_tasks = {
            entry.get("task", "")
            for entry in pair.get("history", [])
            if isinstance(entry, dict)
        }
        if pair.get("task_text"):
            used_tasks.add(pair["task_text"])
        fresh_choices = [item for item in available if item[1] not in used_tasks]
        choices = fresh_choices or [
            item for item in available if item[1] != pair.get("task_text")
        ] or available
        if not choices:
            continue

        if pair.get("task_text"):
            pair.setdefault("history", []).append({
                "date": pair.get("task_date", ""),
                "task": pair.get("task_text", ""),
                "category": pair.get("task_category", ""),
                "answers": dict(pair.get("answers", {})),
            })

        category, task_text = random.choice(choices)
        pair["task_category"] = category
        pair["task_text"] = task_text
        pair["task_date"] = today
        pair["task_completed"] = False
        pair["answers"] = {}
        try:
            save_data()
        except OSError as error:
            print(f"Neizdevās saglabāt automātisko uzdevumu pārim {pair_id}: {error}")
            continue

        mode_label = MODE_LABELS.get(mode, MODE_LABELS["random"])
        try:
            await channel.send(
                f"🌅 **Labrīt! Dienas uzdevums — {today}**\n"
                f"**Kategorija:** {category}\n"
                f"**Režīms:** {mode_label}\n\n"
                f"{task_text}\n\n"
                "Katrs iesniedz savu atbildi ar /answer. Ja uzdevums kādam nav pieņemams, "
                "izvēlieties citu uzdevumu vai nomainiet režīmu."
            )
        except discord.HTTPException as error:
            print(f"Neizdevās nosūtīt automātisko uzdevumu pārim {pair_id}: {error}")


@tasks.loop(minutes=1)
async def daily_task_scheduler():
    await publish_automatic_daily_tasks()


@daily_task_scheduler.before_loop
async def before_daily_task_scheduler():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    if not getattr(bot, "_task_mode_view_registered", False):
        bot.add_view(TaskModeView())
        bot._task_mode_view_registered = True
    if not daily_task_scheduler.is_running():
        daily_task_scheduler.start()
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
            "category": pair.get("task_category", ""),
            "answers": dict(pair.get("answers", {})),
        }
        if pair.get("task_text"):
            pair.setdefault("history", []).append(previous)

        mode = pair.get("task_mode", "random")
        if mode not in TASKS:
            mode = "random"
            pair["task_mode"] = mode
        if mode == "random":
            available = [
                (category, text)
                for group in TASKS.values()
                for category, text in group
            ]
        else:
            available = list(TASKS[mode])

        used_tasks = {
            entry.get("task", "")
            for entry in pair.get("history", [])
            if isinstance(entry, dict)
        }
        if pair.get("task_text"):
            used_tasks.add(pair["task_text"])
        fresh_choices = [item for item in available if item[1] not in used_tasks]
        choices = fresh_choices or [
            item for item in available if item[1] != pair.get("task_text")
        ] or available
        category, task_text = random.choice(choices)
        pair["task_category"] = category
        pair["task_text"] = task_text
        pair["task_date"] = today
        pair["task_completed"] = False
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
        mode_label = MODE_LABELS.get(pair.get("task_mode", "random"), MODE_LABELS["random"])
        await channel.send(
            f"📅 **Dienas uzdevums — {today}**\n"
            f"**Kategorija:** {pair.get('task_category', 'Izaicinājums')}\n"
            f"**Režīms:** {mode_label}\n\n"
            f"{pair['task_text']}\n\n"
            "Katrs iesniedz savu atbildi ar /answer. Ja uzdevums kādam nav pieņemams, "
            "izvēlieties citu uzdevumu vai nomainiet režīmu."
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
    name="task_mode",
    description="Izvēlies uzdevumus kopā, attālināti vai nejauši",
)
async def task_mode(interaction: discord.Interaction):
    _, pair = get_pair_for_user(interaction.user.id)
    if not pair or not user_is_in_guild_pair(interaction, pair):
        await interaction.response.send_message(
            "Vispirms izveido pāri ar /pair_invite un izmanto sava pāra serveri.",
            ephemeral=True,
        )
        return
    current_mode = pair.get("task_mode", "random")
    await interaction.response.send_message(
        f"Pašreizējais režīms: **{MODE_LABELS.get(current_mode, MODE_LABELS['random'])}**\n"
        "Izvēlieties režīmu. Tas paliks spēkā, līdz to nomainīsiet.",
        view=TaskModeView(),
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
    completed_now = False
    if len(pair["answers"]) >= 2 and not pair.get("task_completed", False):
        pair["task_completed"] = True
        pair["completed_tasks"] = int(pair.get("completed_tasks", 0)) + 1
        last_date = pair.get("last_completed_date", "")
        today = today_string()
        if last_date == today:
            pass
        elif last_date:
            try:
                previous_day = datetime.fromisoformat(last_date).date()
                current_day = datetime.fromisoformat(today).date()
                pair["streak"] = int(pair.get("streak", 0)) + 1 if (current_day - previous_day).days == 1 else 1
            except ValueError:
                pair["streak"] = 1
        else:
            pair["streak"] = 1
        pair["last_completed_date"] = today
        completed_now = True
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
    completion_note = (
        f"\n🎉 Uzdevums izpildīts! Kopā izpildīti: {pair.get('completed_tasks', 0)}. "
        f"Pašreizējā sērija: {pair.get('streak', 0)} dienas."
        if pair.get("task_completed", False)
        else ""
    )
    await interaction.response.send_message(
        f"Atbilde saglabāta. Iesniegtas {submitted_count}/2 atbildes šodienas uzdevumam."
        f"{completion_note}",
        ephemeral=True,
    )


@bot.tree.command(
    name="stats",
    description="Parāda pāra uzdevumu statistiku",
)
async def stats(interaction: discord.Interaction):
    _, pair = get_pair_for_user(interaction.user.id)
    if not pair or not user_is_in_guild_pair(interaction, pair):
        await interaction.response.send_message(
            "Vispirms izveido pāri ar /pair_invite un izmanto sava pāra serveri.",
            ephemeral=True,
        )
        return
    completed = int(pair.get("completed_tasks", 0))
    streak = int(pair.get("streak", 0))
    last_date = pair.get("last_completed_date") or "Pagaidām nav"
    answers = pair.get("answers", {})
    await interaction.response.send_message(
        f"📊 **Jūsu pāra statistika**\n"
        f"✅ Kopā izpildīti uzdevumi: **{completed}**\n"
        f"🔥 Pašreizējā dienu sērija: **{streak}**\n"
        f"📅 Pēdējais izpildītais uzdevums: **{last_date}**\n"
        f"✍️ Šodien iesniegtās atbildes: **{len(answers)}/2**",
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
