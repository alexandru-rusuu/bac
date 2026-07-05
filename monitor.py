#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor Bacalaureat 2026.

Verifica pagina de Noutati si directoarele de rezultate ale site-ului
https://static.bacalaureat.edu.ro/2026/ si trimite o notificare pe Telegram
imediat ce apar rezultatele (sau orice modificare relevanta).

Fara dependinte externe - foloseste doar biblioteca standard Python.
"""

import hashlib
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

# Consola Windows nu suporta emoji implicit; forteaza UTF-8 la afisare.
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass

# Ora Romaniei vara (EEST = UTC+3). Pentru afisare in notificari.
RO_TZ = timezone(timedelta(hours=3))

BASE = "https://static.bacalaureat.edu.ro/2026"
TARGETS = {
    "news": f"{BASE}/info/news.html",          # <- Noutati (semnalul principal)
    "rapoarte": f"{BASE}/rapoarte/",           # rezultate prima sesiune (iunie-iulie)
    "rapoarte_sept": f"{BASE}/rapoarte_sept/", # rezultate sesiunea a doua (august)
}

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "state.json")
UA = "Mozilla/5.0 (compatible; BacMonitor2026/1.0; +github-actions)"

# Recunoaste o propozitie de tipul "Rezultatele ... au fost publicate".
# [^.]{0,200} = ramane in interiorul unei singure propozitii (nu sare peste puncte).
RES_SENT = re.compile(r"rezultat[^.]{0,200}?publicat[\wăâîșşțţ]*", re.IGNORECASE)


def now_ro() -> str:
    return datetime.now(RO_TZ).strftime("%d.%m.%Y %H:%M:%S")


def fetch(url: str, tries: int = 3) -> str:
    """Descarca o pagina si o decodeaza din windows-1250 (encoding-ul site-ului)."""
    last = None
    for _ in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=25) as r:
                raw = r.read()
            return raw.decode("windows-1250", errors="replace")
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


def visible_text(html_src: str) -> str:
    """
    Extrage doar textul VIZIBIL dintr-o pagina:
    - scoate comentariile HTML (site-ul tine anunturile viitoare comentate!)
    - scoate <script>/<style>
    - scoate tagurile si decodeaza entitatile
    """
    h = re.sub(r"<!--.*?-->", " ", html_src, flags=re.S)
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<[^>]+>", " ", h)
    h = html.unescape(h)
    h = re.sub(r"\s+", " ", h).strip()
    return h


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def results_sentences(text: str) -> list:
    """Toate propozitiile de tip 'Rezultate ... publicate', normalizate."""
    out = []
    for m in RES_SENT.findall(text):
        s = re.sub(r"\s+", " ", m).strip()
        if s and s not in out:
            out.append(s)
    return out


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:  # noqa: BLE001
            pass
    return {}


def save_state(st: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)


def telegram(text: str) -> bool:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("!! Lipsesc TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID. Mesajul ar fi fost:\n", text)
        return False
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode(
        {
            "chat_id": chat,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }
    ).encode()
    try:
        req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=25) as r:
            r.read()
        print("-> Notificare Telegram trimisa.")
        return True
    except urllib.error.HTTPError as e:
        print("!! Eroare Telegram HTTP:", e.code, e.read().decode("utf-8", "replace"))
    except Exception as e:  # noqa: BLE001
        print("!! Eroare Telegram:", e)
    return False


def main() -> int:
    # Mod de test: TEST_ALERT=1 python monitor.py  -> trimite un mesaj de proba
    if os.environ.get("TEST_ALERT"):
        telegram(f"🔔 <b>Test notificare</b> — monitorul functioneaza.\n⏰ {now_ro()} (ora RO)")
        return 0

    st = load_state()

    fetched = {}
    for key, url in TARGETS.items():
        try:
            fetched[key] = fetch(url)
        except Exception as e:  # noqa: BLE001
            print(f"!! Nu am putut descarca {key} ({url}): {e}")

    if "news" not in fetched:
        # Fara pagina principala nu putem decide nimic; nu modificam starea.
        print("Pagina de Noutati indisponibila momentan. Ies fara modificari.")
        return 0

    news_text = visible_text(fetched["news"])
    cur_results = results_sentences(news_text)

    hashes = st.get("hashes", {})
    seen_results = st.get("seen_results", [])

    # ---- PRIMA rulare: stabileste baseline + confirmare ca merge Telegram ----
    if not st.get("initialized"):
        telegram(
            "✅ <b>Monitor Bacalaureat 2026 pornit cu succes!</b>\n\n"
            f"Verific automat la fiecare ~5 minute:\n{TARGETS['news']}\n\n"
            "Primesti o notificare 🔔 imediat ce apar rezultatele.\n"
            f"⏰ {now_ro()} (ora RO)"
        )
        save_state(
            {
                "initialized": True,
                "hashes": {k: sha(visible_text(v)) for k, v in fetched.items()},
                "seen_results": cur_results,  # ce e deja acolo NU e o noutate
                "last_checked": now_ro(),
            }
        )
        return 0

    alerts = []

    # ---- 1) REZULTATE noi in Noutati (semnalul principal) ----
    new_results = [s for s in cur_results if s not in seen_results]
    if new_results:
        detalii = "\n".join(f"• {s}" for s in new_results)
        alerts.append(
            "🎉🎉🎉 <b>AU APĂRUT REZULTATELE LA BACALAUREAT 2026!</b> 🎉🎉🎉\n\n"
            f"{detalii}\n\n"
            f"📊 Rezultate: {BASE}/rapoarte/\n"
            f"👉 Noutăți: {TARGETS['news']}\n"
            f"⏰ {now_ro()} (ora RO)"
        )
        seen_results = seen_results + new_results

    # ---- 2) Noutati s-a modificat, dar fara anunt de rezultate (informativ) ----
    news_hash = sha(news_text)
    if not new_results and news_hash != hashes.get("news"):
        preview = news_text[:600] + ("…" if len(news_text) > 600 else "")
        alerts.append(
            "ℹ️ <b>Site-ul Bacalaureat 2026 s-a modificat</b> (secțiunea Noutăți)\n\n"
            f"{preview}\n\n"
            f"👉 {TARGETS['news']}\n"
            f"⏰ {now_ro()} (ora RO)"
        )

    # ---- 3) Continutul directoarelor de rezultate s-a schimbat (early warning) ----
    for key in ("rapoarte", "rapoarte_sept"):
        if key not in fetched:
            continue
        hv = sha(visible_text(fetched[key]))
        old = hashes.get(key)
        if old is not None and hv != old:
            sess = "prima sesiune (iunie-iulie)" if key == "rapoarte" else "a doua sesiune (august)"
            alerts.append(
                f"⚠️ <b>Posibil rezultate încărcate — {sess}</b>\n"
                f"Conținutul directorului de rezultate s-a modificat "
                f"(poate aparea inainte de anuntul oficial).\n\n"
                f"👉 {BASE}/{key}/\n"
                f"⏰ {now_ro()} (ora RO)"
            )

    for a in alerts:
        telegram(a)

    # ---- Actualizeaza starea ----
    for key, v in fetched.items():
        hashes[key] = sha(visible_text(v))
    st.update(
        {
            "initialized": True,
            "hashes": hashes,
            "seen_results": seen_results,
            "last_checked": now_ro(),
        }
    )
    save_state(st)

    if not alerts:
        print(f"[{now_ro()}] Nicio modificare. (rezultate cunoscute: {len(seen_results)})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
