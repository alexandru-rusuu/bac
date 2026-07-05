# Monitor Bacalaureat 2026

Verifică automat site-ul <https://static.bacalaureat.edu.ro/2026/> la fiecare câteva secunde și
trimite o notificare pe **Telegram** la orice modificare — și un anunț clar în momentul în care se
publică rezultatele. Fără dependințe externe, doar Python standard.

Ce monitorizează:
- `info/news.html` — secțiunea Noutăți (semnalul principal: anunțul de rezultate)
- `index.html` — pagina principală
- `rapoarte/` și `rapoarte_sept/` — directoarele de rezultate (early-warning)

Detectează separat sesiunea 1 (iunie-iulie) și sesiunea a 2-a (august).

---

## Partea 1 — Botul de Telegram (o singură dată)

1. În Telegram, caută **@BotFather**, dă `/newbot`, alege un nume și un username.
   Primești un **token** de forma `123456789:AAExxxxxxxxxxxxxxxxxxxx`.
2. Deschide botul tău nou și apasă **Start** (trimite-i orice mesaj).
3. Află **chat_id**-ul tău: deschide în browser (înlocuiește `<TOKEN>`):
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
   Caută `"chat":{"id":123456789,...}` — numărul acela e chat_id-ul tău.
   (Dacă e gol, trimite întâi un mesaj botului și reîncarcă pagina.)

Notează cele două valori — le folosești la pasul următor.

---

## Partea 2 — Rulare pe DigitalOcean (droplet)

Cel mai mic droplet costă ~$4/lună (~$1 pe săptămână), deci creditul de $5 acoperă peste o lună.

### 1. Creează dropletul
- În DigitalOcean: **Create → Droplets**
- Imagine: **Ubuntu** (ultima versiune LTS)
- Plan: **Basic → Regular → $4/lună** (512 MB e suficient)
- Regiune: **Frankfurt** sau **Amsterdam** (aproape de România)
- Autentificare: SSH key sau parolă (parola e mai simplă)
- Apasă **Create Droplet**

### 2. Intră pe server
Cel mai simplu: în pagina dropletului → **Access → Launch Droplet Console** (terminal direct în browser, fără SSH).

### 3. Instalează și pornește (copiază comenzile)

```bash
# Python + git
apt update && apt install -y python3 git

# Adu codul (înlocuiește cu repo-ul tău, sau vezi nota de mai jos)
git clone https://github.com/UTILIZATORUL_TAU/bac-monitor.git /opt/bac-monitor

# Pune tokenul și chat_id-ul într-un fișier separat (nu în cod)
nano /etc/bac-monitor.env
```

În `nano`, scrie (cu valorile tale), apoi salvează cu **Ctrl+O, Enter, Ctrl+X**:
```
TELEGRAM_BOT_TOKEN=123456789:AAExxxxxxxxxxxxxxxxxxxx
TELEGRAM_CHAT_ID=123456789
```

Continuă:
```bash
# Instalează serviciul care rulează non-stop și pornește automat la reboot
cp /opt/bac-monitor/bac-monitor.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now bac-monitor

# Verifică
systemctl status bac-monitor --no-pager
```

Imediat ar trebui să primești pe Telegram mesajul **„Monitor Bacalaureat 2026 activ"**.
Gata — verifică singur la 15 secunde, non-stop, și te anunță la orice modificare.

### Comenzi utile
```bash
journalctl -u bac-monitor -f          # vezi log-ul live
systemctl restart bac-monitor         # repornește
systemctl stop bac-monitor            # oprește
nano /etc/bac-monitor.env             # schimbă tokenul/chat_id (apoi restart)
```

> **Nota (fără GitHub):** dacă nu vrei să pui codul pe GitHub, poți crea fișierele direct pe server:
> `mkdir -p /opt/bac-monitor && nano /opt/bac-monitor/monitor.py` (lipești conținutul), la fel pentru
> `bac-monitor.service`. Restul comenzilor rămân identice.

---

## Reglaje

- **Cât de des verifică:** schimbă `Environment=CHECK_INTERVAL=15` (secunde) în
  `/etc/systemd/system/bac-monitor.service`, apoi `systemctl daemon-reload && systemctl restart bac-monitor`.
- **Test notificare:** `TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... TEST_ALERT=1 python3 monitor.py`
- **Stare:** `state.json` (creat lângă script) reține ce a fost deja văzut, ca să nu primești același anunț de două ori.

---

## Alternativă gratuită: GitHub Actions

Repo-ul include și `.github/workflows/monitor.yml`, care rulează același `monitor.py` gratuit pe
GitHub Actions (verificare la ~30 sec, fără server). Folosește-l **doar dacă NU** rulezi pe droplet —
altfel primești notificări duble. Detalii: pune secretele `TELEGRAM_BOT_TOKEN` și `TELEGRAM_CHAT_ID`
în Settings → Secrets → Actions, fă repo-ul public și activează workflow-ul din tab-ul Actions.
