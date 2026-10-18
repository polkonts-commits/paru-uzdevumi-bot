# Pāru uzdevumu Discord bots

Discord bots pāru izveidei, privātām istabām, ikdienas uzdevumiem un atbilžu vēsturei.

## Funkcijas

- `/pair_invite` — uzaicina servera dalībnieku izveidot pāri.
- `/task` — parāda pašreizējo uzdevumu vai izsniedz pirmo uzdevumu pārim.
- Jauns uzdevums tiek izsūtīts katru dienu **plkst. 09.00 pēc Latvijas laika**.
- Atbildes un izpildes apstiprinājumus var iesniegt līdz nākamajai plkst. 09.00. Ja abi uzdevumu pabeidz agrāk, izsūtīšanas laiks nemainās.
- Plkst. 09.00 iepriekšējais uzdevums nonāk vēsturē un tiek izsūtīts nākamais. Nepabeigtais uzdevums un tā statuss tiek saglabāts vēsturē.
- `/answer teksts` — saglabā lietotāja atbildi un apstiprina iesniegšanu.
- Uzdevumu atbildes tiek nosūtītas partneriem privāti Discord DM; bots saglabā atbildes un uzdevumu vēsturi `data.json` failā.
- `/unpair` — pēc apstiprinājuma dzēš pāra kanālus un pāra datus no bota datu faila.

Izsūtīšanas grafiks un atbilžu termiņi izmanto Latvijas laika zonu (`Europe/Riga`), arī pārejot pāri pusnaktij vai mainoties vasaras/ziemas laikam.

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
