"""Polish strings for the DRS bot."""

GEN_EMOJI = "<:Genesis:1409872792211554365>"
ENR_EMOJI = "<:Enrich:1409872795600424960>"
RSE_EMOJI = "<:ModTRSE:1256962175398842399>"
_11_EMOJI = "<:11:1378449282688090184>"
_12_EMOJI = "<:12:1378449310831607828>"

STRINGS: dict = {
    "queue_title": "⭐ Kolejka Ciemnej Czerwonej Gwiazdy",
    "queue_empty": "*Brak pilotów w hangarze. Wciśnij numer, aby wystartować!*",
    "queue_footer": "Aktualizacja co minutę · Kliknij poziom, aby dołączyć lub wyjść",
    "queue_legend": f"> -# `Przełącz kolejkę `: 7️⃣–{_12_EMOJI}\n> -# `Opuść kolejkę(s)`: ❌\n> -# `Ustaw Technologie`: {GEN_EMOJI} {ENR_EMOJI} {RSE_EMOJI}\n> -# `Dodaj Czas(30m)`: ⏳\n> -# `Start Duo       `: ▶️",
    "joined": [
        "✅ Dołączono do **DRS{level}**! Zegar: {time}\n📋 W kolejkach: **{levels}**",
        "🚀 **DRS{level}** potwierdzony — {time} na zegarze.\n📋 Aktywne: **{levels}**",
        "⚡ Gotowy na **DRS{level}**! {time} do końca.\n📋 W kolejce: **{levels}**",
        "🎯 Jesteś w **DRS{level}** — {time} do wygaśnięcia.\n📋 W kolejkach: **{levels}**",
        "💫 **DRS{level}** — dołączono! {time} na liczniku.\n📋 Aktywne kolejki: **{levels}**",
    ],
    "left_level": [
        "👋 Opuszczono **DRS{level}**. Nadal w: **{levels}**",
        "✈️ Wyrzucony z **DRS{level}**. Pozostało: **{levels}**",
        "🚪 Poza **DRS{level}**. Nadal w kolejkach: **{levels}**",
    ],
    "left_level_all_gone": [
        "👋 Opuszczono **DRS{level}**. Jesteś wolny od kolejek.",
        "🚪 Wyszedłeś z **DRS{level}** — wszystko czyste.",
        "✈️ Wyrzucony z **DRS{level}**. Brak aktywnych kolejek.",
    ],
    "left_all": [
        "🚪 Opuszczono wszystkie kolejki ({levels}). Do zobaczenia na następnym rajdzie!",
        "👋 Wyszedłeś z {levels}. Kolejka czysta.",
        "✈️ Wyrzucony z {levels}. Gotowy kiedy tylko chcesz!",
    ],
    "not_in_queue": [
        "🤔 Nie jesteś teraz w żadnej kolejce.",
        "❓ Nie znaleziono aktywnych kolejek.",
        "🛸 Jeszcze nigdzie nie jesteś zapisany.",
    ],
    "extended": [
        "⏳ Przedłużono wszystkie kolejki o **{mins} min** ({levels}). Zegar zresetowany!",
        "🕐 +{mins} minut dodane do {levels}. Masz czas!",
        "⌛ Twoje miejsca w {levels} przedłużone o **{mins} min**.",
    ],
    "match_formed": [
        "🔥 **DRS{level}** znaleziono mecz! Sprawdź wątek — czas start!",
        "⚡ Drużyna zebrana dla **DRS{level}**! Wątek jest aktywny.",
        "🚀 Mecz zablokowany dla **DRS{level}**! Przejdź do wątku.",
    ],
    "qs_not_queued": [
        "❓ Nie jesteś w żadnej kolejce. Najpierw dołącz do poziomu DRS.",
        "🤔 Nie można szybko rozpocząć — najpierw dołącz do kolejki!",
    ],
    "qs_multi_queue": [
        "⚠️ Jesteś w wielu kolejkach ({levels}).\nZostaw wszystkie poza jedną przed użyciem ▶️.",
        "❌ Szybki start wymaga jednej kolejki. Jesteś w: {levels}\nNajpierw opuść pozostałe.",
    ],
    "qs_alone": [
        "🧍 Jesteś jedynym w **DRS{level}** w tej chwili. Potrzeba co najmniej 2!",
        "👀 Nikt więcej w **DRS{level}** jeszcze. Szybki start wymaga partnera.",
    ],
    "qs_already": [
        "⏳ Już zasygnalizowano ▶️. Oczekiwanie na potwierdzenie partnera.",
        "🔔 Szybki start oczekuje — piłka po ich stronie!",
    ],
    "qs_confirmed": [
        "🚀 Szybki start potwierdzony! **DRS{level}** startuje. Sprawdź wątek!",
        "⚡ Obaj piloci gotowi — **DRS{level}** startuje! Zobacz wątek.",
    ],
    "qs_sent": [
        "▶️ Szybki start wysłany dla **DRS{level}**! Oczekiwanie na drugiego pilota.",
        "📡 Sygnał wysłany! Partner powiadomiony. Oczekuj potwierdzenia.",
    ],
    "mod_set": [
        "✅ **{mod}** ustawiony na poziom **{level}**. Gotowy!",
        "💾 **{mod}** → **{level}** zapisano. Technologia zaktualizowana!",
        "⚙️ Przyjęto — **{mod}** jest teraz **{level}**.",
    ],
    "mod_prompt": "Twój poziom **{mod}** to obecnie **{current}**.\nWybierz swój nowy poziom:",
    "mod_not_set": "nie ustawiono",
    "notify_left": [
        "👋 **{name}** opuścił kolejkę **DRS{level}**.",
        "🚪 **{name}** wyszedł z **DRS{level}**.",
        "✈️ **{name}** wyrzucony z kolejki **DRS{level}**.",
    ],
    "notify_extend": [
        "⏳ {role}**{name}** przedłużył swoje miejsce w **DRS{level}** o 30 minut.",
        "🕐 {role}**{name}** odświeżył **DRS{level}** — jeszcze 30 minut!",
        "⌛ {role}**{name}** doładował timer w **DRS{level}**. Kolejka wciąż żywa!",
    ],
    "expiry_warning": [
        "⏰ **{name}** — twoje miejsce w **DRS{level}** wygasa za ~5 minut! Kliknij ⏳ aby dodać 30.",
        "🚨 **{name}** — czas w DRS{level} prawie upłynął! Przedłuż teraz albo wypadniesz.",
        "⌛ **{name}** — 5 minut do końca w **DRS{level}**. Dodaj czas, jeśli chcesz zachować miejsce!",
    ],
    "expiry_extend_prompt": "⏳ Dodaj 30 min",
    "expiry_extended_ok": "✅ Dodano 30 minut do twojej kolejki **DRS{level}**!",
    "expiry_not_yours": "🤔 Ten przycisk przedłużenia nie jest dla ciebie.",
    "match_proceed": [
        "✅ Mecz **DRS{level}** gotowy — proszę kontynuować! Powodzenia piloci 🚀",
        "🚀 **DRS{level}** drużyna w komplecie — wchodźcie gdy gotowi!",
        "⭐ Wszyscy piloci potwierdzeni na **DRS{level}** — lećcie bezpiecznie!",
    ],
    "notify_match_formed": [
        "✅ **DRS{level}** mecz utworzony — {size}/{size} pilotów potwierdzonych. Kolejka zresetowana.",
        "🚀 **DRS{level}** startuje — pełny skład ({size}/{size})!",
        "⭐ **DRS{level}** mecz skompletowany — {size}/{size}. Powodzenia!",
    ],
    "notify_joined_title": "📡 Nadlatujący Pilot — DRS{level}",
    "notify_joined": [
        "**{name}** właśnie dołączył do **DRS{level}**! {spots} miejsce/a zostało — kto dołączy?",
        "🚀 **{name}** jest zablokowany na **DRS{level}**. {spots} slot(y) wolne!",
        "⚡ **{name}** wszedł do DRS{level}. {spots} więcej potrzebnych — nie przegap!",
        "🎯 **{name}** gotowy na **DRS{level}**! {spots} miejsce/a wolne.",
        "🌟 **{name}** dołączył do **DRS{level}**. Miejsce dla {spots} pilotów!",
        "📻 Nadlatujący pilot! **{name}** w kolejce do **DRS{level}** — {spots} dostępne.",
        "💫 **{name}** chce polecieć **DRS{level}**! {spots} slot(y) do wzięcia.",
        "🛸 **{name}** zarejestrowany na **DRS{level}**. {spots} więcej do startu!",
        "🔥 **{name}** gotowy spalić **DRS{level}**! {spots} miejsce/a zostało.",
        "⭐ **{name}** w kolejce do **DRS{level}**. {spots} wolnych — wskakuj!",
    ],
    "notify_qs_title": "▶️ Szybki Start — DRS{level}",
    "notify_qs": [
        "**{name}** chce polecieć **DRS{level}** tylko w 2! Kliknij ▶️ na kolejce, aby potwierdzić.",
        "🚀 **{name}** rwie się do lotu **DRS{level}** — proponowany rajd 2-osobowy! Wciśnij ▶️.",
        "⚡ Rajd 2-osobowy! **{name}** chce rozpocząć **DRS{level}** teraz. Kliknij ▶️!",
    ],
    "match_title": "⭐ Ciemna Czerwona Gwiazda {level} — Mecz #{match_id}",
    "match_footer": "Powodzenia — niech gwiazdy wam sprzyjają 🌟",
    "match_warning": [
        "⚡ **{names}** — ogarnijcie technologię przed skokiem!",
        "⚠️ **{names}** — zaktualizujcie modyfikacje przed startem!",
        "🔧 **{names}** — przygotujcie technologię, potem lecimy!",
    ],
    "match_warning_multi": [
        "⚡ **{names}** — ogarnijcie technologię przed skokiem!",
        "⚠️ Niektórzy piloci nie ustawili technologii. **{names}** — aktualizacja przed startem!",
    ],
    "feedback_prompt": "🏁 Jak poszedł rajd DRS?",
    "feedback_thanks": [
        "Dzięki za opinię! Galaktyka bezpieczna. 🌌",
        "Zanotowane! Liczy się każdy lot. 🚀",
        "Opinia przyjęta — doceniamy! ⭐",
    ],
    "feedback_not_participant": "❌ Tylko uczestnicy meczu mogą przesłać opinię.",
    "feedback_already_submitted": "✅ Już przesłałeś opinię dla tego meczu.",
    "feedback_no_others": "🤔 Brak innych graczy do zgłoszenia w tym meczu.",
    "feedback_select_player": "Kogo chcesz zgłosić? Wybierz gracza poniżej:",
    "feedback_error": "❌ Nie udało się zapisać opinii. Spróbuj ponownie?",
    "report_thanks": [
        "✅ Zgłoszenie dla **{name}** wysłane. Oficerowie zostali powiadomieni.",
        "📋 **{name}** oznaczony do przeglądu.",
    ],
    "officer_alert_title": "⚠️ Zgłoszenie Negatywnego Rajdu",
    "setup_success_title": "✅ DRS Bot Skonfigurowany",
    "setup_footer": "Wiadomość kolejki opublikowana na kanale kolejki.",
    "setup_roles_success": "✅ Role pingowania zaktualizowane!",
    "setup_no_auth": "❌ Potrzebujesz uprawnień Administratora lub roli menedżera.",
    "status_not_setup": "⚠️ Jeszcze nie skonfigurowano. Uruchom `/drs setup` najpierw.",
    "status_title": "DRS Bot — Konfiguracja Serwera",
    "lang_set": "✅ Język ustawiony na **{lang}**.",
}
