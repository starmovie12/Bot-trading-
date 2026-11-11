# OWNER_START: Recorder shuru karne ki guide (simple Hinglish)

**Sabse pehle sach:** Recorder abhi asli Upstox feed se **nahi** judta. Asli feed ka "adapter" (Upstox ka
data padhne wala hissa) abhi bana nahi, kyunki Upstox feed ka official format is session mein verify nahi
ho saka (web band tha: INCIDENT #1). Isliye abhi tum sirf **dry-run** chala sakte ho: ye nakli data par
machine ko jaanchta hai, kuch save nahi karta, kisi broker se nahi judta, koi order nahi lagata.

## Pehla sawal: PC ya phone?

Chat mein jawab do: `haan F-MACHINE 9a0b` (phone, Termux) ya `na F-MACHINE 9a0b` (PC).
Jab tak jawab nahi, LIGHT scope chalega (dono par safe).

## 5 kadam

1. **Download:** bundle file `recorder_bundle_<tareekh>.zip` agent ke file panel se lo (ya branch pull karo,
   agar `F-REMOTE` manzoor ho).
2. **Unzip:** kisi bhi folder mein kholo. Andar `SHA256SUMS` hai: har file ka hash.
3. **Token (abhi nahi):** asli feed bante hi token set-up ka tareeka yahan aayega. Niyam pakka hai: token
   sirf tumhari machine par, bundle folder ke **bahar**, file permission 600, aur kabhi data pack mein nahi.
   Token kabhi chat mein ya agent ko mat do.
4. **Dry-run:** bundle folder ke andar ye ek command:
   `python3 -m bot.recorder --dry-run`
5. **Roz ka start (baad mein):** asli feed bante hi yahan ek command aayegi. Abhi `--live` likhoge to
   Recorder saaf mana karega ("REFUSED"), aur ye sahi hai.

## Phone (Termux) settings (sirf agar phone chuna)

- `termux-wake-lock` chalao, Termux ki battery optimisation OFF karo, charger laga rakho, Termux ki
  notification band mat karo.
- Phone par sirf LIGHT scope.

## PC settings (sirf agar PC chuna)

- Bazaar ke samay (08:45 se 16:00 IST) PC sleep band.
- Ghadi (time) automatic rakho (internet time / NTP on).

## Roz ka kaam (5 minute se kam, asli feed ke baad)

Start, health line dekho, shaam ko band. Health line: `python3 -m bot.recorder --health <din ki file>`.

## OK kaisa dikhta hai

- Dry-run: `DRY-RUN OK: 72 instruments, 27000 messages, 0 alerts, nothing saved`
- Health: `OK: coverage 100.0%, missing 0, duplicates 0`

## NOT OK ho to kya karein

- Kuch mat badlo, dobara-dobara mat chalao. Poori line copy karke agent ko do (`continue` ke saath note).
- `size_cap_80` dikhe: disk bharne wali hai; data pack bana kar agent ko do (`python3 tools/pack_data.py`),
  phir purani copy apne backup mein rakho. Recorder khud kuch delete nahi karta.
- `disk_full` dikhe: Recorder ruk gaya hai; jagah khali karo, phir agle din chalao.
- `clock_drift` dikhe: machine ka time automatic (NTP) karo.

## Data agent tak kaise pahunchega

`python3 tools/pack_data.py` ek `datapack_<se>_<tak>.zip` banata hai (sirf din ki sealed files, checksum ke
saath; token kabhi nahi). Ise agent ke workspace mein upload karo aur chat mein likho: `continue data <file>`.
