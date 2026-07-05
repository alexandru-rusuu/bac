# Monitor Bacalaureat 2026 🔔

Verifică automat site-ul <https://static.bacalaureat.edu.ro/2026/> **la ~30 de secunde** și îți
trimite o **notificare instant pe Telegram** la orice modificare — și un anunț special când apar
rezultatele. Ca să nu mai dai tu refresh.

Rulează gratuit pe **GitHub Actions**. Zero server, zero mentenanță.

> ⚠️ **Fă repo-ul PUBLIC.** Pe repo-uri publice minutele de GitHub Actions sunt **nelimitate și gratis**,
> deci monitorul poate rula non-stop. Pe repo privat ai doar ~2000 min/lună și s-ar consuma repede.
> (Nu pui nimic secret în cod — tokenul stă în Secrets, nu în fișiere.)

## Ce monitorizează

- `info/news.html` — secțiunea **Noutăți** (semnalul principal: anunțul „Rezultatele ... au fost publicate")
- `rapoarte/` și `rapoarte_sept/` — directoarele de rezultate (early-warning: dacă se încarcă înainte de anunț)

Detectează separat **sesiunea 1** (iunie-iulie) și **sesiunea a 2-a** (august), deci merge tot anul.

---

## Setup (o singură dată, ~10 minute)

### 1. Fă-ți un bot de Telegram
1. În Telegram, caută **@BotFather** și dă-i `/newbot`.
2. Alege un nume și un username. Primești un **token** de forma `123456789:AAExxxxxxxxxxxxxxxxxxxx`.
3. Caută botul tău nou și apasă **Start** (trimite-i orice mesaj, ex. `salut`).

### 2. Află `chat_id`-ul tău
1. Deschide în browser (înlocuiește `<TOKEN>` cu tokenul tău):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
2. Caută în răspuns `"chat":{"id":123456789,...}`. Numărul acela e **chat_id**-ul tău.
   - Dacă e gol, trimite întâi un mesaj botului și reîncarcă pagina.

### 3. Pune codul pe GitHub
1. Creează un repo nou pe GitHub (ex. `bac-monitor`).
2. Urcă fișierele din acest folder (vezi comenzile de mai jos).

### 4. Adaugă secretele în repo
În repo → **Settings → Secrets and variables → Actions → New repository secret**, adaugă:

| Nume | Valoare |
|------|---------|
| `TELEGRAM_BOT_TOKEN` | tokenul de la BotFather |
| `TELEGRAM_CHAT_ID` | chat_id-ul tău |

### 5. Activează și testează
1. Tab-ul **Actions** → dacă îți cere, apasă „I understand my workflows, go ahead and enable them".
2. Selectează **Monitor Bacalaureat 2026** → **Run workflow** (pornire manuală).
3. Ar trebui să primești pe Telegram mesajul: **„✅ Monitor Bacalaureat 2026 pornit cu succes!"**

Gata. De acum verifică singur la ~5 minute și te anunță când apar rezultatele. 🎉

---

## Comenzi git pentru a urca pe GitHub

```bash
git init
git add .
git commit -m "Monitor Bacalaureat 2026"
git branch -M main
git remote add origin https://github.com/UTILIZATORUL_TAU/bac-monitor.git
git push -u origin main
```

---

## Note

- **Rapiditate (~30 sec):** GitHub nu permite cron sub 5 minute, dar fiecare job rulează o buclă
  internă care verifică la fiecare **30 de secunde** timp de ~16 minute; cron-ul repornește jobul
  la 15 min → acoperire continuă. Poți schimba viteza din `CHECK_INTERVAL` (secunde) în
  [.github/workflows/monitor.yml](.github/workflows/monitor.yml).
- **Test manual al notificării:** rulează local `TEST_ALERT=1 python monitor.py`
  (cu variabilele `TELEGRAM_BOT_TOKEN` și `TELEGRAM_CHAT_ID` setate) ca să primești un mesaj de probă.
- **Stare:** `state.json` reține ce a fost deja văzut ca să nu primești același anunț de mai multe ori.
  E salvat automat în repo de către workflow.
- Fără dependințe externe — doar Python standard.

### Bonus: rulare pe VM pentru viteză maximă (opțional)

Pe un server Linux (ex. droplet DigitalOcean), pune un cron la fiecare minut:
```bash
* * * * * TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=yyy /usr/bin/python3 /cale/catre/monitor.py >> /var/log/bac.log 2>&1
```
Același `monitor.py` funcționează identic; folosește `state.json` din același folder.
