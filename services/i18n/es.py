"""Spanish strings for the DRS bot."""

GEN_EMOJI = "<:Genesis:1519930122566635652>"
ENR_EMOJI = "<:Enrich:1519930167005413466>"
RSE_EMOJI = "<:ModTRSE:1256962175398842399>"
_11_EMOJI = "<:11:1378449282688090184>"
_12_EMOJI = "<:12:1519933592401215570>"

STRINGS: dict = {
    # Pinned Queue Embed Titles & Texts
    "queue_title_drs": "Cola Estrella Roja Oscura",
    "queue_title_rs": "Cola Estrella Roja",
    "queue_empty_drs": "*No hay pilotos en el hangar. ¡Toca un botón de nivel abajo para despegar!*",
    "queue_empty_rs": "*No hay pilotos en la cola Estrella Roja. ¡Selecciona un nivel abajo para formar escuadrón!*",
    "queue_title": "⭐ Cola Estrella Roja Oscura",
    "queue_empty": "*No hay pilotos en el hangar. ¡Pulsa un número para entrar!*",
    "queue_footer": "Actualiza cada minuto · Toca un nivel para unirte o salir",
    "queue_legend": f"> -# `Cambiar Cola`: 7️⃣–{_12_EMOJI}\n> -# `Salir Cola(s)`: ❌\n> -# `Config Tech  `: {GEN_EMOJI} {ENR_EMOJI} {RSE_EMOJI}\n> -# `Añadir(30m)  `: ⏳\n> -# `Inicio Dúo   `: ▶️",

    # Channel Notifications (Broadcasts)
    "notify_joined": [
        "{icon}El piloto **{pilot}** se unió a **{queue}** {count} · Listo para el salto",
        "{icon}El piloto **{pilot}** se unió a **{queue}** {count} · En cubierta de vuelo",
        "{icon}El piloto **{pilot}** se unió a **{queue}** {count} · Sistemas activos",
    ],
    "notify_left": [
        "🚪 {icon}El piloto **{pilot}** salió de **{queue}** · Desacoplado",
        "🚪 {icon}El piloto **{pilot}** salió de **{queue}** · Regreso a la estación",
        "🚪 {icon}El piloto **{pilot}** salió de **{queue}** · Espera cancelada",
    ],
    "notify_left_all": [
        "🚪 {icon}El piloto **{pilot}** salió de todas las colas ({queues}) · Regreso a la estación",
        "🚪 {icon}El piloto **{pilot}** salió de todas las colas ({queues}) · Plan de vuelo cerrado",
    ],
    "notify_qs": [
        "⚡ {icon}{users}El piloto **{pilot}** activó Inicio Rápido para **{queue}** {count}",
        "⚡ {icon}{users}El piloto **{pilot}** solicitó Inicio Rápido para **{queue}** {count}",
    ],
    "notify_extend": [
        "⏳ {icon}El piloto **{pilot}** extendió su turno de vuelo en **{queue}** (+30m)",
    ],
    "notify_assist": [
        "🆘 {icon}El piloto **{pilot}** solicitó escolta de flota para **{queue}**",
    ],
    "notify_expiry_warning": [
        "⚠️ {icon}Piloto <@{user_id}>: tu turno en **{queue}** expira en **5 min** (toca ⏳ para renovar)",
    ],
    "notify_expired": [
        "⏰ {icon}El piloto <@{user_id}> salió de **{queue}** · Turno expirado",
        "⏰ {icon}Piloto <@{user_id}> retirado de **{queue}** · Tiempo de sensor agotado",
    ],
    "notify_match_formed_title": [
        "⚔️ ¡Flota de {queue} Nivel {level} Formada! (Partida #{match_id})",
        "🚀 ¡Flota Reunida: {queue}{level}! (Partida #{match_id})",
        "💥 ¡Grupo de Combate Listo: {queue}{level}! (Partida #{match_id})",
    ],
    "notify_match_formed_desc": [
        "⏱️ **Formada en:** {duration}\n\n**Pilotos en Cubierta:**\n{roster}\n\n🛰️ *¡Coordenadas de salto fijadas! Revisa el hilo de la partida.*",
        "⏱️ **Tiempo de reunión:** {duration}\n\n**Escuadrón:**\n{roster}\n\n🔥 *Armas calientes, escudos listos. ¡Al hilo de combate!*",
    ],

    # Personal Ephemeral Responses
    "ephemeral_joined": [
        "✅ ¡Registrado en **{queue}**! Cuenta regresiva iniciada (30m). ¡Alerta a tus compañeros!",
        "✅ Autorización concedida para **{queue}**. Tienes 30 minutos antes de expirar.",
        "✅ Cabina sellada. Estás en cola para **{queue}** (30m). ¡Buena caza!",
    ],
    "ephemeral_left": [
        "👋 Desacoplado de **{queue}**. Compuertas del hangar abiertas.",
        "👋 Retirado de **{queue}**. ¡Descansa, piloto!",
        "👋 Has salido de **{queue}**.",
    ],
    "ephemeral_left_all": [
        "🚪 Saliste de todas las colas activas. Pistas despejadas.",
        "🚪 Sistemas apagados. Has salido de todas las colas.",
    ],
    "ephemeral_extended": [
        "⏳ ¡Extendiste tu turno (**{queues}**) por +30 minutos! Bobinas estables.",
        "⏳ ¡+30 minutos añadidos a **{queues}**! Tiempo de sobra para repostar.",
    ],
    "ephemeral_qs": [
        "⚡ ¡Inicio Rápido activado para **{queue}**! Listos para saltar con 2+ pilotos.",
        "⚡ Sobremarcha activada en **{queue}**. ¡Modo sin espera habilitado!",
    ],
    "ephemeral_assist_on": [
        "🆘 ¡Pedir Ayuda activado (**ON**)! Tu baliza de auxilio alertará a otros comandantes.",
    ],
    "ephemeral_assist_off": [
        "✅ Pedir Ayuda desactivado (**OFF**). Protocolo estándar de vuelo restaurado.",
    ],

    # Legacy & Modals
    "joined": [
        "✅ ¡Registrado en **{queue}**! Tiempo: {time}\n📋 Colas activas: **{levels}**",
        "🚀 **{queue}** confirmado — {time}.\n📋 Activo: **{levels}**",
        "⚡ ¡Listo para **{queue}**! {time}.\n📋 En cola: **{levels}**",
    ],
    "left_level": [
        "👋 Saliste de **{queue}**. Sigues en: **{levels}**",
    ],
    "left_level_all_gone": [
        "👋 Saliste de **{queue}** — sin colas activas.",
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
        "🔥 ¡Partida para **{queue}**! Revisa el hilo.",
    ],
    "qs_not_queued": [
        "❓ No estás en ninguna cola. ¡Únete primero!",
    ],
    "qs_multi_queue": [
        "⚠️ Estás en varias colas ({levels}). Deja todas menos una para ▶️.",
    ],
    "qs_alone": [
        "🧍 Eres el único en **{queue}**. Se necesitan mínimo 2.",
    ],
    "qs_already": [
        "⏳ Ya presionaste ▶️. Esperando al otro jugador.",
    ],
    "qs_confirmed": [
        "🚀 ¡Inicio rápido confirmado! **{queue}** en marcha.",
    ],
    "qs_sent": [
        "▶️ Solicitud enviada para **{queue}**. Esperando confirmación.",
    ],
    "mod_set": [
        "✅ **{mod}** nivel **{level}** guardado.",
        "💾 **{mod}** → **{level}** ¡guardado!",
    ],
    "mod_prompt": "Tu nivel de **{mod}** actual: **{current}**\nElige el nuevo nivel:",
    "mod_not_set": "no definido",
    "expiry_warning": [
        "⏰ **{name}** — ¡tu puesto en **{queue}** expira en ~5 minutos! Toca ⏳ para añadir 30.",
        "🚨 **{name}** — ¡tiempo casi agotado en {queue}!",
    ],
    "expiry_extend_prompt": "⏳ +30 min",
    "expiry_extended_ok": "✅ ¡Añadidos 30 minutos a tu cola **{queue}**!",
    "expiry_not_yours": "🤔 Este botón no es para ti.",
    "match_proceed": [
        "✅ ¡Partida de **{queue}** formada — procedan pilotos! 🚀",
        "🚀 Escuadrón **{queue}** listo — ¡entren cuando quieran!",
    ],
    "match_title": "⭐ {queue} — Partida #{match_id}",
    "match_footer": "Buena suerte — que las estrellas los guíen 🌟",
    "match_warning": [
        "⚡ **{names}** — ¡configura tus módulos antes de saltar!",
    ],
    "match_warning_multi": [
        "⚡ **{names}** — ¡configura tus módulos antes de saltar!",
    ],
    "feedback_prompt": "🏁 ¿Cómo fue la partida?",
    "feedback_thanks": [
        "¡Gracias por tu opinión! 🌌",
        "¡Anotado! 🚀",
    ],
    "feedback_not_participant": "❌ Solo los participantes pueden enviar comentarios.",
    "feedback_already_submitted": "✅ Ya enviaste comentarios sobre esta partida.",
    "feedback_no_others": "🤔 No hay otros jugadores que reportar.",
    "feedback_select_player": "¿A quién quieres reportar? Selecciona abajo:",
    "feedback_error": "❌ Error al registrar. ¿Intentas de nuevo?",
    "report_thanks": [
        "✅ Reporte enviado sobre **{name}** a los oficiales.",
    ],
    "officer_alert_title": "⚠️ Reporte Negativo",
    "setup_success_title": "✅ Bot Configurado",
    "setup_footer": "Mensaje de cola publicado en el canal.",
    "setup_roles_success": "✅ ¡Roles de ping actualizados!",
    "setup_no_auth": "❌ Necesitas permiso de Administrador o rol de manager.",
    "status_not_setup": "⚠️ No configurado aún. Ejecuta `/drs setup` primero.",
    "status_title": "Bot de Cola — Configuración",
    "lang_set": "✅ Idioma configurado a **{lang}**.",
}
