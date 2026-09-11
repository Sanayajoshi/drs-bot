"""Polish strings for the DRS bot."""

GEN_EMOJI = "<:Genesis:1519930122566635652>"
ENR_EMOJI = "<:Enrich:1519930167005413466>"
RSE_EMOJI = "<:ModTRSE:1256962175398842399>"
_11_EMOJI = "<:11:1378449282688090184>"
_12_EMOJI = "<:12:1519933592401215570>"

STRINGS: dict = {
    # Pinned Queue Embed Titles & Texts
    "queue_title_drs": "Kolejka Ciemnej Czerwonej Gwiazdy",
    "queue_title_rs": "Kolejka Czerwonej Gwiazdy",
    "queue_empty_drs": "*Brak pilotów w hangarze. Kliknij przycisk poziomu poniżej, aby wystartować!*",
    "queue_empty_rs": "*Brak pilotów w kolejce RS. Wybierz poziom poniżej, aby sformować flotę!*",
    "queue_title": "⭐ Kolejka Ciemnej Czerwonej Gwiazdy",
    "queue_empty": "*Brak pilotów w hangarze. Wciśnij numer, aby wystartować!*",
    "queue_footer": "Aktualizacja co minutę · Kliknij poziom, aby dołączyć lub wyjść",
    "queue_legend": f"> -# `Przełącz kolejkę `: 7️⃣–{_12_EMOJI}\n> -# `Opuść kolejkę(s)`: ❌\n> -# `Ustaw Technologie`: {GEN_EMOJI} {ENR_EMOJI} {RSE_EMOJI}\n> -# `Dodaj Czas(30m)`: ⏳\n> -# `Start Duo       `: ▶️",

    # Channel Notifications (Broadcasts)
    "notify_joined": [
        "{icon}Pilot **{pilot}** dołączył do **{queue}** {count} · Gotowy do skoku",
        "{icon}Pilot **{pilot}** dołączył do **{queue}** {count} · Na pokładzie startowym",
        "{icon}Pilot **{pilot}** dołączył do **{queue}** {count} · Systemy aktywne",
    ],
    "notify_left": [
        "🚪 {icon}Pilot **{pilot}** opuścił **{queue}** · Odcumowano",
        "🚪 {icon}Pilot **{pilot}** opuścił **{queue}** · Powrót do stacji",
        "🚪 {icon}Pilot **{pilot}** opuścił **{queue}** · Gotowość odwołana",
    ],
    "notify_left_all": [
        "🚪 {icon}Pilot **{pilot}** opuścił wszystkie kolejki ({queues}) · Powrót do stacji",
        "🚪 {icon}Pilot **{pilot}** opuścił wszystkie kolejki ({queues}) · Plan lotu zamknięty",
    ],
    "notify_qs": [
        "⚡ {icon}{users}Pilot **{pilot}** włączył Szybki Start dla **{queue}** {count}",
        "⚡ {icon}{users}Pilot **{pilot}** zażądał Szybkiego Startu dla **{queue}** {count}",
    ],
    "notify_extend": [
        "⏳ {icon}Pilot **{pilot}** przedłużył slot lotu w **{queue}** (+30m)",
    ],
    "notify_assist": [
        "🆘 {icon}Pilot **{pilot}** prosi o eskortę floty dla **{queue}**",
    ],
    "notify_expiry_warning": [
        "⚠️ {icon}Pilot <@{user_id}>: slot w **{queue}** wygasa za **5 min** (kliknij ⏳, aby przedłużyć)",
    ],
    "notify_expired": [
        "⏰ {icon}Pilot <@{user_id}> opuścił **{queue}** · Slot wygasł",
        "⏰ {icon}Pilot <@{user_id}> usunięty z **{queue}** · Poza zasięgiem czujników",
    ],
    "notify_match_formed_title": [
        "⚔️ Flota {queue} Poziom {level} Sformowana! (Mecz #{match_id})",
        "🚀 Flota Zebrana: {queue}{level}! (Mecz #{match_id})",
        "💥 Grupa Bojowa Gotowa: {queue}{level}! (Mecz #{match_id})",
    ],
    "notify_match_formed_desc": [
        "⏱️ **Czas formowania:** {duration}\n\n**Piloci na pokładzie:**\n{roster}\n\n🛰️ *Współrzędne skoku zablokowane! Sprawdź wątek meczu!*",
        "⏱️ **Czas zbiórki:** {duration}\n\n**Skład eskadry:**\n{roster}\n\n🔥 *Uzbrojenie aktywne, tarcze naładowane. Do wątku meczu!*",
    ],

    # Personal Ephemeral Responses
    "ephemeral_joined": [
        "✅ Zapisano do **{queue}**! Odliczanie rozpoczęte (30m). Oczekuj na skrzydłowych!",
        "✅ Zgoda na start przyznana dla **{queue}** (30 minut ważności).",
        "✅ Kokpit zamknięty! Jesteś w kolejce do **{queue}** (30m). Udanych łowów!",
    ],
    "ephemeral_left": [
        "👋 Odłączono od **{queue}**. Wrota hangaru otwarte.",
        "👋 Wycofano z **{queue}**. Odpocznij, pilocie!",
    ],
    "ephemeral_left_all": [
        "🚪 Opuszczono wszystkie aktywne kolejki. Pasy startowe czyste.",
        "🚪 Statki wyłączone. Jesteś poza wszystkimi kolejkami.",
    ],
    "ephemeral_extended": [
        "⏳ Przedłużono czas w kolejkach (**{queues}**) o +30 minut!",
        "⏳ +30 minut dodane do **{queues}**! Czas na zatankowanie paliwa.",
    ],
    "ephemeral_qs": [
        "⚡ Szybki Start włączony dla **{queue}**! Gotowość do lotu przy 2+ pilotach.",
    ],
    "ephemeral_assist_on": [
        "🆘 Prośba o pomoc włączona (**ON**)! Flota widzi twój sygnał ratunkowy.",
    ],
    "ephemeral_assist_off": [
        "✅ Prośba o pomoc wyłączona (**OFF**). Standardowy profil lotu.",
    ],

    # Legacy & Modals
    "joined": [
        "✅ Dołączono do **{queue}**! Zegar: {time}\n📋 W kolejkach: **{levels}**",
        "🚀 **{queue}** potwierdzony — {time} na zegarze.\n📋 Aktywne: **{levels}**",
    ],
    "left_level": [
        "👋 Opuszczono **{queue}**. Nadal w: **{levels}**",
    ],
    "left_level_all_gone": [
        "👋 Opuszczono **{queue}**. Jesteś wolny od kolejek.",
    ],
    "left_all": [
        "🚪 Opuszczono wszystkie kolejki ({levels}). Do zobaczenia na następnym rajdzie!",
    ],
    "not_in_queue": [
        "🤔 Nie jesteś teraz w żadnej kolejce.",
    ],
    "extended": [
        "⏳ Przedłużono wszystkie kolejki o **{mins} min** ({levels}). Zegar zresetowany!",
    ],
    "match_formed": [
        "🔥 **{queue}** znaleziono mecz! Sprawdź wątek — czas start!",
    ],
    "qs_not_queued": [
        "❓ Nie jesteś w żadnej kolejce. Najpierw dołącz do poziomu.",
    ],
    "qs_multi_queue": [
        "⚠️ Jesteś w wielu kolejkach ({levels}).\nZostaw wszystkie poza jedną przed użyciem ▶️.",
    ],
    "qs_alone": [
        "🧍 Jesteś jedynym w **{queue}** w tej chwili. Potrzeba co najmniej 2!",
    ],
    "qs_already": [
        "⏳ Już wcisnąłeś ▶️. Czekam na drugiego gracza.",
    ],
    "qs_confirmed": [
        "🚀 Szybki start potwierdzony! **{queue}** rusza!",
    ],
    "qs_sent": [
        "▶️ Wysłano prośbę o szybki start dla **{queue}**! Czekam na potwierdzenie.",
    ],
    "mod_set": [
        "✅ **{mod}** ustawiony na poziom **{level}**.",
    ],
    "mod_prompt": "Twój aktualny poziom **{mod}**: **{current}**\nWybierz nowy poziom:",
    "mod_not_set": "nie ustawiono",
    "expiry_warning": [
        "⏰ **{name}** — twój slot w **{queue}** wygasa za ~5 minut! Kliknij ⏳.",
    ],
    "expiry_extend_prompt": "⏳ Dodaj 30 min",
    "expiry_extended_ok": "✅ Dodano 30 minut do twojej kolejki **{queue}**!",
    "expiry_not_yours": "🤔 Ten przycisk nie jest dla ciebie.",
    "match_proceed": [
        "✅ **{queue}** mecz ukończony — ruszajcie piloci! 🚀",
    ],
    "match_title": "⭐ {queue} — Mecz #{match_id}",
    "match_footer": "Powodzenia — niech gwiazdy wam sprzyjają 🌟",
    "match_warning": [
        "⚡ **{names}** — ustaw technologie przed wejściem w nadprzestrzeń!",
    ],
    "match_warning_multi": [
        "⚡ **{names}** — ustaw technologie przed wejściem w nadprzestrzeń!",
    ],
    "feedback_prompt": "🏁 Jak poszedł rajd?",
    "feedback_thanks": [
        "Dzięki za opinię! 🌌",
    ],
    "feedback_not_participant": "❌ Tylko uczestnicy meczu mogą przesyłać opinie.",
    "feedback_already_submitted": "✅ Już przesłałeś opinię dla tego meczu.",
    "feedback_no_others": "🤔 Brak innych graczy do zgłoszenia w tym meczu.",
    "feedback_select_player": "Kogo chcesz zgłosić? Wybierz gracza poniżej:",
    "feedback_error": "❌ Nie udało się zapisać opinii. Spróbować ponownie?",
    "report_thanks": [
        "✅ Zgłoszenie dla **{name}** zostało wysłane. Oficerowie zostali powiadomieni.",
    ],
    "officer_alert_title": "⚠️ Negatywny Raport z Rajdu",
    "setup_success_title": "✅ Bot Skonfigurowany",
    "setup_footer": "Wiadomość z kolejką opublikowana na kanale.",
    "setup_roles_success": "✅ Role do powiadomień zaktualizowane!",
    "setup_no_auth": "❌ Wymagane uprawnienia Administratora lub rola managera.",
    "status_not_setup": "⚠️ Jeszcze nie skonfigurowano. Uruchom najpierw `/drs setup`.",
    "status_title": "Bot Kolejkowy — Konfiguracja Serwera",
    "lang_set": "✅ Język ustawiony na **{lang}**.",
}
