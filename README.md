# Pāru uzdevumu Discord bots

Discord bots pāru izveidei, privātām istabām, ikdienas uzdevumiem un atbilžu vēsturei.

## Funkcijas

- `/pair_invite` — uzaicina servera dalībnieku izveidot pāri.
- `/task` — publicē vienu dienas uzdevumu; atkārtota komandas lietošana tajā pašā dienā neizveido jaunu uzdevumu.
- `/answer teksts` — saglabā lietotāja atbildi un apstiprina iesniegšanu.
- `/unpair` — pēc apstiprinājuma dzēš pāra kanālus un pāra datus no bota datu faila.

Dienas datums tiek aprēķināts pēc Latvijas laika zonas (`Europe/Riga`).

## Palaišana

Nepieciešams Python 3.10 vai jaunāks.

1. Instalē atkarības:

   ```bash
   python -m pip install -r requirements.txt
   ```

2. Discord Developer Portal izveido botu un nokopē tokenu. **Nekad nepublicē tokenu GitHub un neievieto to kodā.**
3. Iestati vides mainīgo `DISCORD_TOKEN`.

   Linux/macOS:
   ```bash
   export DISCORD_TOKEN="tavs_discord_bota_tokens"
   python main.py
   ```

   Windows PowerShell:
   ```powershell
   $env:DISCORD_TOKEN="tavs_discord_bota_tokens"
   python main.py
   ```

4. Ielūdz botu serverī ar `bot` un `applications.commands` OAuth2 tvērumiem.
5. Piešķir botam atļaujas veidot un dzēst kanālus/kategorijas, skatīt kanālus, sūtīt ziņas un lasīt ziņu vēsturi.


## Nejaušie komplimenti

- Ja servera dalībnieks piemin botu, tas atbild ar nejaušu komplimentu latviešu valodā.
- Ir sešas kategorijas: smieklīgi, draudzīgi, nedaudz sarkastiski, motivējoši, romantiski un flirtējoši.
- Funkcija reaģē tikai uz tiešu bota pieminējumu servera ziņā. Tā neanalizē visas čata ziņas.
- Šai funkcijai nav jāieslēdz **Message Content Intent**; Discord nodrošina ziņas informāciju gadījumos, kad bots ir pieminēts.
- Botam vajadzīga atļauja **View Channels** un **Send Messages** attiecīgajā kanālā.

## Datu glabāšana

Pāri, dienas uzdevumi un atbildes tiek glabāti lokālajā `data.json` failā. Ja hostinga vide dzēš lokālos failus pēc restartēšanas, izmanto pastāvīgu disku vai datubāzi. Neizdzēs `data.json`, ja vēlies saglabāt pašreizējo bota stāvokli.

## Piezīmes

- Botam jābūt ieslēgtam, lai atbildētu uz slash komandām.
- Ja bots tiek palaists no jauna, Discord slash komandas tiek sinhronizētas automātiski.
- Pāra izveidei un noņemšanai botam vajadzīga Discord atļauja **Manage Channels**.
- Šajā repozitorijā nav iekļauts bota tokens.
