"""German strings for the DRS bot."""

GEN_EMOJI = "<:Genesis:1409872792211554365>"
ENR_EMOJI = "<:Enrich:1409872795600424960>"
RSE_EMOJI = "<:ModTRSE:1256962175398842399>"
_11_EMOJI = "<:11:1378449282688090184>"
_12_EMOJI = "<:12:1378449310831607828>"

STRINGS: dict = {
    "queue_title": "⭐ Dunkler Roter Stern — Warteschlange",
    "queue_empty": "*Keine Piloten. Drück eine Zahl zum Beitreten!*",
    "queue_footer": "Aktualisiert jede Minute · Tippe eine Stufe zum Beitreten/Verlassen",
    "queue_legend": f"> -# `Queue umschalten`: 7️⃣–{_12_EMOJI}\n> -# `Queue verlassen `: ❌\n> -# `Tech setzen     `: {GEN_EMOJI} {ENR_EMOJI} {RSE_EMOJI}\n> -# `Zeit(30m)       `: ⏳\n> -# `Duo-Start       `: ▶️",
    "joined": [
        "✅ Du bist in **DRS{level}** eingetragen! Zeit: {time}\n📋 Aktive Queues: **{levels}**",
        "🚀 **DRS{level}** bestätigt! Timer: {time}.\n📋 In Warteschlange: **{levels}**",
    ],
    "left_level": [
        "👋 Du hast **DRS{level}** verlassen. Noch dabei: **{levels}**",
    ],
    "left_level_all_gone": [
        "👋 **DRS{level}** verlassen — keine aktiven Queues mehr.",
    ],
    "left_all": [
        "🚪 Alle Queues verlassen ({levels}). Bis zum nächsten Mal!",
    ],
    "not_in_queue": [
        "🤔 Du bist in keiner Warteschlange.",
    ],
    "extended": [
        "⏳ Deine Queues {levels} um **{mins} Min** verlängert!",
        "🕐 +{mins} Min zu {levels} hinzugefügt!",
    ],
    "match_formed": [
        "🔥 **DRS{level}** Match gefunden! Schau in den Thread.",
        "⚡ Squad für **DRS{level}** bereit! Thread ist live.",
    ],
    "qs_not_queued": [
        "❓ Du bist in keiner Queue. Tritt erst einem DRS-Level bei!",
    ],
    "qs_multi_queue": [
        "⚠️ Du bist in mehreren Queues ({levels}). Verlasse alle außer einer für ▶️.",
    ],
    "qs_alone": [
        "🧍 Du bist allein in **DRS{level}**. Mindestens 2 Spieler nötig!",
    ],
    "qs_already": [
        "⏳ Du hast bereits ▶️ gedrückt. Warte auf den anderen Spieler.",
    ],
    "qs_confirmed": [
        "🚀 Schnellstart bestätigt! **DRS{level}** startet! Schau in den Thread.",
    ],
    "qs_sent": [
        "▶️ Schnellstart für **DRS{level}** angefragt! Warte auf Bestätigung.",
    ],
    "mod_set": [
        "✅ **{mod}** auf Stufe **{level}** gesetzt.",
        "💾 **{mod}** → **{level}** gespeichert!",
    ],
    "mod_prompt": "Dein aktuelles **{mod}**-Level: **{current}**\nWähle das neue Level:",
    "mod_not_set": "nicht gesetzt",
    "notify_left": [
        "👋 **{name}** hat die **DRS{level}**-Queue verlassen.",
        "🚪 **{name}** ist aus **DRS{level}** ausgetreten.",
    ],
    "notify_extend": [
        "⏳ {role}**{name}** hat den **DRS{level}**-Slot um 30 Minuten verlängert.",
        "🕐 {role}**{name}** hat **DRS{level}** aufgefrischt — noch 30 Minuten!",
    ],
    "expiry_warning": [
        "⏰ **{name}** — dein **DRS{level}**-Slot läuft in ~5 Minuten ab! Drücke ⏳ für +30 Min.",
        "🚨 **{name}** — DRS{level} Timer läuft fast ab! Jetzt verlängern oder rausfliegen.",
    ],
    "expiry_extend_prompt": "⏳ +30 Min",
    "expiry_extended_ok": "✅ 30 Minuten zu deiner **DRS{level}**-Queue hinzugefügt!",
    "expiry_not_yours": "🤔 Dieser Button ist nicht für dich.",
    "match_proceed": [
        "✅ **DRS{level}** Match bereit — bitte los! Viel Erfolg Piloten 🚀",
        "🚀 **DRS{level}** Squad komplett — wenn ihr bereit seid, rein da!",
    ],
    "notify_match_formed": [
        "✅ **DRS{level}** Match gebildet — {size}/{size} Piloten. Queue zurückgesetzt!",
    ],
    "notify_joined_title": "📡 Pilot eingetroffen — DRS{level}",
    "notify_joined": [
        "**{name}** hat sich für **DRS{level}** angemeldet! {spots} Platz/Plätze frei — wer kommt mit?",
        "🚀 **{name}** ist bereit für **DRS{level}**! {spots} Slot(s) verfügbar.",
        "⚡ **{name}** in der DRS{level}-Queue. Noch {spots} gesucht!",
        "🎯 **{name}** eingetragen für **DRS{level}**. {spots} Platz/Plätze offen.",
        "🌟 **{name}** in **DRS{level}**. Noch {spots} Pilot(en) gesucht!",
        "📻 Neuer Pilot! **{name}** für **DRS{level}** — {spots} Platz/Plätze frei.",
        "💫 **{name}** will **DRS{level}** fliegen! {spots} Slot(s) offen.",
        "🛸 **{name}** angemeldet für **DRS{level}**. Noch {spots} zum Start!",
        "🔥 **{name}** in **DRS{level}**. {spots} Platz/Plätze frei.",
        "⭐ **{name}** wartet in **DRS{level}**. {spots} Slot(s) verfügbar!",
    ],
    "notify_qs_title": "▶️ Schnellstart — DRS{level}",
    "notify_qs": [
        "**{name}** möchte **DRS{level}** zu zweit starten! Drücke ▶️ zum Bestätigen.",
        "🚀 **{name}** schlägt einen 2-Spieler-Run für **DRS{level}** vor! ▶️ drücken!",
    ],
    "match_title": "⭐ Dunkler Roter Stern {level} — Match #{match_id}",
    "match_footer": "Viel Erfolg — mögen die Sterne mit euch sein! 🌟",
    "match_warning": [
        "⚡ **{names}** — Tech einstellen vor dem Start!",
        "⚠️ **{names}** — Tech-Daten fehlen. Vor dem Start eintragen!",
    ],
    "match_warning_multi": [
        "⚠️ **{names}** — Tech-Daten fehlen. Bitte vor dem Start eintragen!",
    ],
    "feedback_prompt": "🏁 Wie war der DRS-Run?",
    "feedback_thanks": [
        "Danke für dein Feedback! 🌌",
        "Notiert! 🚀",
        "Feedback erhalten — danke! ⭐",
    ],
    "feedback_not_participant": "❌ Nur Match-Teilnehmer können Feedback geben.",
    "feedback_already_submitted": "✅ Du hast bereits Feedback für dieses Match abgegeben.",
    "feedback_no_others": "🤔 Keine anderen Spieler zum Melden in diesem Match.",
    "feedback_select_player": "Wen möchtest du melden? Wähle einen Spieler aus:",
    "feedback_error": "❌ Feedback konnte nicht gespeichert werden. Nochmal versuchen?",
    "report_thanks": [
        "✅ Meldung für **{name}** eingereicht. Offiziere wurden benachrichtigt.",
        "📋 **{name}** wurde zur Überprüfung markiert.",
    ],
    "officer_alert_title": "⚠️ Negativbericht",
    "setup_success_title": "✅ DRS Bot Konfiguriert",
    "setup_footer": "Queue-Nachricht im Queue-Kanal gepostet.",
    "setup_roles_success": "✅ Ping-Rollen aktualisiert!",
    "setup_no_auth": "❌ Du benötigst Administratorrechte oder die Manager-Rolle.",
    "status_not_setup": "⚠️ Noch nicht konfiguriert. Führe `/drs setup` aus.",
    "status_title": "DRS Bot — Server-Konfiguration",
    "lang_set": "✅ Sprache auf **{lang}** gesetzt.",
}
