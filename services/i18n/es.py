"""Spanish strings for the DRS bot."""

GEN_EMOJI = "<:Genesis:1409872792211554365>"
ENR_EMOJI = "<:Enrich:1409872795600424960>"
RSE_EMOJI = "<:ModTRSE:1256962175398842399>"
_11_EMOJI = "<:11:1378449282688090184>"
_12_EMOJI = "<:12:1378449310831607828>"

STRINGS: dict = {
    "queue_title": "⭐ Cola Estrella Roja Oscura",
    "queue_empty": "*No hay pilotos. ¡Pulsa un número para entrar!*",
    "queue_footer": "Actualiza cada minuto · Toca un nivel para unirte o salir",
    "queue_legend": f"> -# `Cambiar Cola`: 7️⃣–{_12_EMOJI}\n> -# `Salir Cola(s)`: ❌\n> -# `Config Tech  `: {GEN_EMOJI} {ENR_EMOJI} {RSE_EMOJI}\n> -# `Añadir(30m)  `: ⏳\n> -# `Inicio Dúo   `: ▶️",
    "joined": [
        "✅ ¡Registrado en **DRS{level}**! Tiempo: {time}\n📋 Colas activas: **{levels}**",
        "🚀 **DRS{level}** confirmado — {time}.\n📋 Activo: **{levels}**",
        "⚡ ¡Listo para **DRS{level}**! {time}.\n📋 En cola: **{levels}**",
    ],
    "left_level": [
        "👋 Saliste de **DRS{level}**. Sigues en: **{levels}**",
    ],
    "left_level_all_gone": [
        "👋 Saliste de **DRS{level}** — sin colas activas.",
    ],
    "left_all": [
        "🚪 Saliste de todas las colas ({levels}). ¡Hasta la próxima!",
    ],
    "not_in_queue": [
        "🤔 No estás en ninguna cola ahora mismo.",
    ],
    "extended": [
        "⏳ Extendiste {levels} **{mins} min** más.",
    ],
    "match_formed": [
        "🔥 ¡Partida para **DRS{level}**! Revisa el hilo.",
    ],
    "qs_not_queued": [
        "❓ No estás en ninguna cola. ¡Únete primero!",
    ],
    "qs_multi_queue": [
        "⚠️ Estás en varias colas ({levels}). Deja todas menos una para ▶️.",
    ],
    "qs_alone": [
        "🧍 Eres el único en **DRS{level}**. Se necesitan mínimo 2.",
    ],
    "qs_already": [
        "⏳ Ya presionaste ▶️. Esperando al otro jugador.",
    ],
    "qs_confirmed": [
        "🚀 ¡Inicio rápido confirmado! **DRS{level}** en marcha.",
    ],
    "qs_sent": [
        "▶️ Solicitud enviada para **DRS{level}**. Esperando confirmación.",
    ],
    "mod_set": [
        "✅ **{mod}** nivel **{level}** guardado.",
        "💾 **{mod}** → **{level}** ¡guardado!",
    ],
    "mod_prompt": "Tu nivel de **{mod}** actual: **{current}**\nElige el nuevo nivel:",
    "mod_not_set": "no definido",
    "notify_left": [
        "👋 **{name}** salió de la cola **DRS{level}**.",
        "🚪 **{name}** abandonó **DRS{level}**.",
    ],
    "notify_extend": [
        "⏳ {role}**{name}** extendió su lugar en **DRS{level}** 30 minutos más.",
        "🕐 {role}**{name}** recargó **DRS{level}** — ¡otros 30 minutos!",
    ],
    "expiry_warning": [
        "⏰ **{name}** — ¡tu slot en **DRS{level}** expira en ~5 minutos! Pulsa ⏳ para añadir 30 más.",
        "🚨 **{name}** — ¡casi sin tiempo en DRS{level}! Extiende ahora o te quedarás fuera.",
    ],
    "expiry_extend_prompt": "⏳ +30 min",
    "expiry_extended_ok": "✅ ¡30 minutos añadidos a tu cola **DRS{level}**!",
    "expiry_not_yours": "🤔 Este botón no es para ti.",
    "match_proceed": [
        "✅ Partida **DRS{level}** completa — ¡adelante, pilotos! 🚀",
        "🚀 Escuadrón **DRS{level}** confirmado — ¡cuando estéis listos!",
    ],
    "notify_match_formed": [
        "✅ Partida **DRS{level}** formada — {size}/{size} pilotos. ¡Cola reiniciada!",
    ],
    "notify_joined_title": "📡 Piloto entrante — DRS{level}",
    "notify_joined": [
        "**{name}** se unió a **DRS{level}**. Quedan {spots} lugar(es) — ¿te apuntas?",
        "🚀 ¡**{name}** listo para **DRS{level}**! {spots} hueco(s) disponibles.",
        "⚡ **{name}** entró a DRS{level}. ¡Faltan {spots} más!",
        "🎯 **{name}** en **DRS{level}**. {spots} puesto(s) libres.",
        "🌟 **{name}** en cola para **DRS{level}**. ¡{spots} más y despegamos!",
        "📻 ¡Nuevo piloto! **{name}** en **DRS{level}** — {spots} libre(s).",
        "💫 **{name}** quiere correr **DRS{level}**. {spots} hueco(s) disponibles.",
        "🛸 **{name}** listo para **DRS{level}**. ¡{spots} más para lanzar!",
        "🔥 **{name}** en **DRS{level}**. Quedan {spots} plaza(s).",
        "⭐ **{name}** en la cola de **DRS{level}**. {spots} libre(s) — ¡súmate!",
    ],
    "notify_qs_title": "▶️ Inicio Rápido — DRS{level}",
    "notify_qs": [
        "**{name}** quiere correr **DRS{level}** con solo 2. Pulsa ▶️.",
        "🚀 **{name}** propone 2 jugadores en **DRS{level}**! Pulsa ▶️.",
    ],
    "match_title": "⭐ Estrella Roja Oscura {level} — Partida #{match_id}",
    "match_footer": "¡Buena suerte — que las estrellas os acompañen! 🌟",
    "match_warning": [
        "⚡ **{names}** — ¡configura tu tech antes de entrar!",
    ],
    "match_warning_multi": [
        "⚠️ **{names}** — poneos al día con el tech antes de lanzar.",
    ],
    "feedback_prompt": "🏁 ¿Cómo fue la carrera DRS?",
    "feedback_thanks": [
        "¡Gracias por tu opinión! 🌌",
        "¡Anotado! 🚀",
        "¡Recibido — gracias! ⭐",
    ],
    "feedback_not_participant": "❌ Solo los participantes del match pueden enviar comentarios.",
    "feedback_already_submitted": "✅ Ya enviaste comentarios para este match.",
    "feedback_no_others": "🤔 No hay otros jugadores para reportar en este match.",
    "feedback_select_player": "¿A quién quieres reportar? Selecciona un jugador:",
    "feedback_error": "❌ No se pudo registrar tu opinión. ¿Lo intentas de nuevo?",
    "report_thanks": [
        "✅ Reporte enviado para **{name}**. Los oficiales han sido notificados.",
        "📋 **{name}** ha sido marcado para revisión.",
    ],
    "officer_alert_title": "⚠️ Reporte Negativo",
    "setup_success_title": "✅ DRS Bot Configurado",
    "setup_footer": "Mensaje de cola publicado.",
    "setup_roles_success": "✅ ¡Roles de ping actualizados!",
    "setup_no_auth": "❌ Necesitas permisos de Administrador o el rol de gestor.",
    "status_not_setup": "⚠️ Sin configurar. Ejecuta `/drs setup` primero.",
    "status_title": "DRS Bot — Configuración",
    "lang_set": "✅ Idioma configurado como **{lang}**.",
}
