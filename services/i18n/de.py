"""German strings for the DRS bot."""

GEN_EMOJI = "<:Genesis:1519930122566635652>"
ENR_EMOJI = "<:Enrich:1519930167005413466>"
RSE_EMOJI = "<:ModTRSE:1256962175398842399>"
_11_EMOJI = "<:11:1378449282688090184>"
_12_EMOJI = "<:12:1519933592401215570>"

STRINGS: dict = {
    # Pinned Queue Embed Titles & Texts
    "queue_title_drs": "Dunkler Roter Stern — Warteschlange",
    "queue_title_rs": "Roter Stern — Warteschlange",
    "queue_empty_drs": "*Keine Piloten im Hangar. Tippe unten auf eine Stufe zum Starten!*",
    "queue_empty_rs": "*Keine Piloten in der Roter-Stern-Warteschlange. Wähle unten eine Stufe für die Flotte!*",
    "queue_title": "⭐ Dunkler Roter Stern — Warteschlange",
    "queue_empty": "*Keine Piloten. Drück eine Zahl zum Beitreten!*",
    "queue_footer": "Aktualisiert jede Minute · Tippe eine Stufe zum Beitreten/Verlassen",
    "queue_legend": f"> -# `Queue umschalten`: 7️⃣–{_12_EMOJI}\n> -# `Queue verlassen `: ❌\n> -# `Tech setzen     `: {GEN_EMOJI} {ENR_EMOJI} {RSE_EMOJI}\n> -# `Zeit(30m)       `: ⏳\n> -# `Duo-Start       `: ▶️",

    # Channel Notifications (Broadcasts)
    "notify_joined": [
        "{icon}Pilot **{pilot}** ist **{queue}** {count} beigetreten · Startbereit",
        "{icon}Pilot **{pilot}** ist **{queue}** {count} beigetreten · Auf dem Flugdeck",
        "{icon}Pilot **{pilot}** ist **{queue}** {count} beigetreten · Systeme aktiv",
    ],
    "notify_left": [
        "🚪 {icon}Pilot **{pilot}** hat **{queue}** verlassen · Abgedockt",
        "🚪 {icon}Pilot **{pilot}** hat **{queue}** verlassen · Rückkehr zur Station",
        "🚪 {icon}Pilot **{pilot}** hat **{queue}** verlassen · Standby abgebrochen",
    ],
    "notify_left_all": [
        "🚪 {icon}Pilot **{pilot}** hat alle Queues verlassen ({queues}) · Rückkehr zur Station",
        "🚪 {icon}Pilot **{pilot}** hat alle Queues verlassen ({queues}) · Flugplan gelöscht",
    ],
    "notify_qs": [
        "⚡ {icon}{users}Pilot **{pilot}** hat Schnellstart für **{queue}** {count} aktiviert",
        "⚡ {icon}{users}Pilot **{pilot}** hat Schnellstart für **{queue}** {count} angefordert",
    ],
    "notify_extend": [
        "⏳ {icon}Pilot **{pilot}** hat Flugslot für **{queue}** verlängert (+30m)",
    ],
    "notify_assist": [
        "🆘 {icon}Pilot **{pilot}** bittet um Flotteneskorte für **{queue}**",
    ],
    "notify_expiry_warning": [
        "⚠️ {icon}Pilot <@{user_id}>: Flugslot in **{queue}** läuft in **5 Min.** ab (tippe ⏳ zum Verlängern)",
    ],
    "notify_expired": [
        "⏰ {icon}Pilot <@{user_id}> hat **{queue}** verlassen · Slot abgelaufen",
        "⏰ {icon}Pilot <@{user_id}> aus **{queue}** entfernt · Sensor-Timeout",
    ],
    "notify_match_formed_title": [
        "⚔️ {queue} Stufe {level} Flotte gebildet! (Match #{match_id})",
        "🚀 Flotte versammelt: {queue}{level}! (Match #{match_id})",
        "💥 Gefechtsgruppe bereit: {queue}{level}! (Match #{match_id})",
    ],
    "notify_match_formed_desc": [
        "⏱️ **Gebildet in:** {duration}\n\n**Piloten an Deck:**\n{roster}\n\n🛰️ *Sprungkoordinaten erfasst! Schau in den Match-Thread für Details!*",
        "⏱️ **Bereitstellungszeit:** {duration}\n\n**Geschwader:**\n{roster}\n\n🔥 *Waffen scharf, Schilde aktiv. Auf in den Match-Thread!*",
    ],

    # Personal Ephemeral Responses
    "ephemeral_joined": [
        "✅ In **{queue}** eingeklinkt! Countdown läuft (30m). Schnall dich an!",
        "✅ Starterlaubnis für **{queue}** erteilt (30 Min. gültig).",
        "✅ Cockpit verriegelt! Du stehst für **{queue}** bereit (30m).",
    ],
    "ephemeral_left": [
        "👋 Von **{queue}** abgemeldet. Hangartore geöffnet.",
        "👋 Aus **{queue}** ausgetragen. Gute Erholung, Pilot!",
        "👋 Slot in **{queue}** freigegeben.",
    ],
    "ephemeral_left_all": [
        "🚪 Alle aktiven Warteschlangen verlassen. Startbahnen frei.",
        "🚪 Schiffe heruntergefahren. Du hast alle Queues verlassen.",
    ],
    "ephemeral_extended": [
        "⏳ Slot(s) (**{queues}**) um +30 Minuten verlängert! Warpspule hält.",
        "⏳ +30 Minuten zu **{queues}** hinzugefügt! Zeit genug zum Auftanken.",
    ],
    "ephemeral_qs": [
        "⚡ Schnellstart für **{queue}** aktiviert! Start ab 2+ Piloten.",
        "⚡ Overdrive aktiv auf **{queue}**! Sofortstart-Modus scharf.",
    ],
    "ephemeral_assist_on": [
        "🆘 Hilferuf aktiviert (**EIN**)! Notfall-Signal leuchtet in der Warteschlange.",
    ],
    "ephemeral_assist_off": [
        "✅ Hilferuf deaktiviert (**AUS**). Standard-Flugmodus aktiv.",
    ],

    # Legacy & Modals
    "joined": [
        "✅ Du bist in **{queue}** eingetragen! Zeit: {time}\n📋 Aktive Queues: **{levels}**",
        "🚀 **{queue}** bestätigt! Timer: {time}.\n📋 In Warteschlange: **{levels}**",
    ],
    "left_level": [
        "👋 Du hast **{queue}** verlassen. Noch dabei: **{levels}**",
    ],
    "left_level_all_gone": [
        "👋 **{queue}** verlassen — keine aktiven Queues mehr.",
    ],
    "left_all": [
        "🚪 Alle Queues verlassen ({levels}). Bis zum nächsten Mal!",
    ],
    "not_in_queue": [
        "🤔 Du bist in keiner Warteschlange.",
    ],
    "extended": [
        "⏳ Deine Queues {levels} um **{mins} Min** verlängert!",
    ],
    "match_formed": [
        "🔥 **{queue}** Match gefunden! Schau in den Thread.",
    ],
    "qs_not_queued": [
        "❓ Du bist in keiner Queue. Tritt erst bei!",
    ],
    "qs_multi_queue": [
        "⚠️ Du bist in mehreren Queues ({levels}). Verlasse alle außer einer für ▶️.",
    ],
    "qs_alone": [
        "🧍 Du bist allein in **{queue}**. Mindestens 2 Spieler nötig!",
    ],
    "qs_already": [
        "⏳ Du hast bereits ▶️ gedrückt. Warte auf den anderen Spieler.",
    ],
    "qs_confirmed": [
        "🚀 Schnellstart bestätigt! **{queue}** startet!",
    ],
    "qs_sent": [
        "▶️ Schnellstart für **{queue}** angefragt! Warte auf Bestätigung.",
    ],
    "mod_set": [
        "✅ **{mod}** auf Stufe **{level}** gesetzt.",
    ],
    "mod_prompt": "Dein aktuelles **{mod}**-Level: **{current}**\nWähle das neue Level:",
    "mod_not_set": "nicht gesetzt",
    "expiry_warning": [
        "⏰ **{name}** — dein Platz in **{queue}** läuft in ~5 Minuten ab! Tippe ⏳ zum Verlängern.",
    ],
    "expiry_extend_prompt": "⏳ +30 Min",
    "expiry_extended_ok": "✅ 30 Minuten zu deiner **{queue}**-Queue hinzugefügt!",
    "expiry_not_yours": "🤔 Dieser Button ist nicht für dich.",
    "match_proceed": [
        "✅ **{queue}** Match komplett — guten Flug Piloten! 🚀",
    ],
    "match_title": "⭐ {queue} — Match #{match_id}",
    "match_footer": "Viel Erfolg — mögen die Sterne günstig stehen 🌟",
    "match_warning": [
        "⚡ **{names}** — rüste deine Module aus, bevor es losgeht!",
    ],
    "match_warning_multi": [
        "⚡ **{names}** — rüste deine Module aus, bevor es losgeht!",
    ],
    "feedback_prompt": "🏁 Wie war der Flug?",
    "feedback_thanks": [
        "Danke für das Feedback! 🌌",
    ],
    "feedback_not_participant": "❌ Nur Match-Teilnehmer können Feedback geben.",
    "feedback_already_submitted": "✅ Du hast bereits Feedback für dieses Match abgegeben.",
    "feedback_no_others": "🤔 Keine anderen Spieler in diesem Match zu melden.",
    "feedback_select_player": "Wen möchtest du melden? Wähle unten einen Spieler:",
    "feedback_error": "❌ Konnte Feedback nicht speichern. Erneut versuchen?",
    "report_thanks": [
        "✅ Meldung für **{name}** eingereicht. Die Offiziere wurden benachrichtigt.",
    ],
    "officer_alert_title": "⚠️ Negativer Spielbericht",
    "setup_success_title": "✅ Bot Konfiguriert",
    "setup_footer": "Queue-Nachricht im Kanal gepostet.",
    "setup_roles_success": "✅ Ping-Rollen aktualisiert!",
    "setup_no_auth": "❌ Administratorrechte oder Manager-Rolle erforderlich.",
    "status_not_setup": "⚠️ Noch nicht konfiguriert. Führe zuerst `/drs setup` aus.",
    "status_title": "Queue Bot — Serverkonfiguration",
    "lang_set": "✅ Sprache auf **{lang}** gesetzt.",
}
