"""French strings for the DRS bot."""

GEN_EMOJI = "<:Genesis:1519930122566635652>"
ENR_EMOJI = "<:Enrich:1519930167005413466>"
RSE_EMOJI = "<:ModTRSE:1256962175398842399>"
_11_EMOJI = "<:11:1378449282688090184>"
_12_EMOJI = "<:12:1519933592401215570>"

STRINGS: dict = {
    # Pinned Queue Embed Titles & Texts
    "queue_title_drs": "File d'attente Étoile Rouge Sombre",
    "queue_title_rs": "File d'attente Étoile Rouge",
    "queue_empty_drs": "*Aucun pilote dans le hangar. Appuie sur un bouton de niveau ci-dessous pour décoller !*",
    "queue_empty_rs": "*Aucun pilote dans la file Étoile Rouge. Sélectionne un niveau pour former une escouade !*",
    "queue_title": "⭐ File d'attente Étoile Rouge Sombre",
    "queue_empty": "*Aucun pilote dans le hangar. Appuie sur un numéro pour décoller !*",
    "queue_footer": "Mise à jour chaque minute · Appuie sur un niveau pour rejoindre ou quitter",
    "queue_legend": f"> -# `Basculer File  `: 7️⃣–{_12_EMOJI}\n> -# `Quitter File(s)`: ❌\n> -# `Config Tech    `: {GEN_EMOJI} {ENR_EMOJI} {RSE_EMOJI}\n> -# `Ajouter(30min) `: ⏳\n> -# `Duo Start      `: ▶️",

    # Channel Notifications (Broadcasts)
    "notify_joined": [
        "{icon}**{pilot}** a rejoint **{queue}** {count}",
        "{icon}**{pilot}** en file pour **{queue}** {count}",
        "{icon}**{pilot}** paré pour **{queue}** {count}",
    ],
    "notify_left": [
        "🚪 {icon}**{pilot}** a quitté **{queue}**",
        "🚪 {icon}**{pilot}** s'est retiré de **{queue}**",
    ],
    "notify_left_all": [
        "🚪 {icon}**{pilot}** a quitté toutes les files ({queues})",
    ],
    "notify_qs": [
        "⚡ {icon}{users}**{pilot}** a activé le Démarrage Rapide pour **{queue}** {count}",
    ],
    "notify_extend": [
        "⏳ {icon}**{pilot}** a prolongé **{queue}** (+30m)",
    ],
    "notify_assist": [
        "🆘 {icon}**{pilot}** demande de l'aide pour **{queue}**",
    ],
    "notify_expiry_warning": [
        "⚠️ {icon}<@{user_id}> : créneau **{queue}** expire dans **5 min** (cliquez sur ⏳ pour prolonger)",
    ],
    "notify_expired": [
        "⏰ {icon}<@{user_id}> retiré de **{queue}** (expiré)",
    ],
    "notify_match_formed_title": [
        "⚔️ Flotte {queue} Niveau {level} Rassemblée ! (Match #{match_id})",
        "🚀 Flotte Prête : {queue}{level} ! (Match #{match_id})",
        "💥 Groupe de Combat Opérationnel : {queue}{level} ! (Match #{match_id})",
    ],
    "notify_match_formed_desc": [
        "⏱️ **Formé en :** {duration}\n\n**Pilotes sur le pont :**\n{roster}\n\n🛰️ *Coordonnées de saut verrouillées ! Rejoignez le fil de match !*",
        "⏱️ **Temps d'assemblage :** {duration}\n\n**Escouade :**\n{roster}\n\n🔥 *Systèmes armés, boucliers levés. Direction le fil de combat !*",
    ],

    # Personal Ephemeral Responses
    "ephemeral_joined": [
        "✅ Enregistré dans **{queue}** ! Compte à rebours lancé (30m). Paré au départ !",
        "✅ Autorisation accordée pour **{queue}** (valide 30 minutes).",
        "✅ Cockpit verrouillé ! Vous êtes en attente pour **{queue}** (30m).",
    ],
    "ephemeral_left": [
        "👋 Désamarré de **{queue}**. Portes du hangar ouvertes.",
        "👋 Retiré de **{queue}**. Reposez-vous, pilote !",
    ],
    "ephemeral_left_all": [
        "🚪 Quitté toutes les files actives. Piste dégagée.",
        "🚪 Vaisseaux éteints. Vous êtes sorti de toutes les files.",
    ],
    "ephemeral_extended": [
        "⏳ Créneau(x) (**{queues}**) prolongé(s) de +30 minutes ! Bobines stables.",
        "⏳ +30 minutes ajoutées à **{queues}** ! Parfait pour refaire le plein.",
    ],
    "ephemeral_qs": [
        "⚡ Démarrage Rapide activé pour **{queue}** ! Prêt à sauter dès 2+ pilotes.",
    ],
    "ephemeral_assist_on": [
        "🆘 Demande d'assistance activée (**ON**) ! Balise de détresse visible dans la file.",
    ],
    "ephemeral_assist_off": [
        "✅ Demande d'assistance désactivée (**OFF**). Mode de vol standard restauré.",
    ],

    # Legacy & Modals
    "joined": [
        "✅ Inscrit pour **{queue}** ! Temps : {time}\n📋 Files actives : **{levels}**",
        "🚀 **{queue}** confirmé — {time} au chrono.\n📋 Actif : **{levels}**",
    ],
    "left_level": [
        "👋 Quitté **{queue}**. Encore dans : **{levels}**",
    ],
    "left_level_all_gone": [
        "👋 Quitté **{queue}**. Plus aucune file active.",
    ],
    "left_all": [
        "🚪 Sorti de toutes les files ({levels}). À la prochaine !",
    ],
    "not_in_queue": [
        "🤔 Tu n'es dans aucune file pour le moment.",
    ],
    "extended": [
        "⏳ Toutes les files prolongées de **{mins} min** ({levels}). Chrono réinitialisé !",
    ],
    "match_formed": [
        "🔥 Match **{queue}** trouvé ! Consulte le fil — c'est l'heure.",
    ],
    "qs_not_queued": [
        "❓ Tu n'es dans aucune file. Rejoins d'abord un niveau.",
    ],
    "qs_multi_queue": [
        "⚠️ Tu es dans plusieurs files ({levels}).\nQuitte toutes sauf une avant d'utiliser ▶️.",
    ],
    "qs_alone": [
        "🧍 Tu es le seul dans **{queue}** pour l'instant. Il faut au moins 2 !",
    ],
    "qs_already": [
        "⏳ Tu as déjà cliqué sur ▶️. En attente de l'autre joueur.",
    ],
    "qs_confirmed": [
        "🚀 Démarrage rapide confirmé ! **{queue}** se lance !",
    ],
    "qs_sent": [
        "▶️ Demande envoyée pour **{queue}** ! En attente de confirmation.",
    ],
    "mod_set": [
        "✅ **{mod}** réglé au niveau **{level}**.",
    ],
    "mod_prompt": "Niveau actuel de **{mod}** : **{current}**\nChoisis le nouveau niveau :",
    "mod_not_set": "non défini",
    "expiry_warning": [
        "⏰ **{name}** — ta place dans **{queue}** expire dans ~5 minutes ! Clique sur ⏳.",
    ],
    "expiry_extend_prompt": "⏳ +30 min",
    "expiry_extended_ok": "✅ 30 minutes ajoutées à ta file **{queue}** !",
    "expiry_not_yours": "🤔 Ce bouton n'est pas pour toi.",
    "match_proceed": [
        "✅ Match **{queue}** complet — bonne chance pilotes ! 🚀",
    ],
    "match_title": "⭐ {queue} — Match #{match_id}",
    "match_footer": "Bonne chance — que les étoiles vous soient favorables 🌟",
    "match_warning": [
        "⚡ **{names}** — configurez vos modules avant le saut !",
    ],
    "match_warning_multi": [
        "⚡ **{names}** — configurez vos modules avant le saut !",
    ],
    "feedback_prompt": "🏁 Comment s'est passée la partie ?",
    "feedback_thanks": [
        "Merci pour le retour ! 🌌",
    ],
    "feedback_not_participant": "❌ Seuls les participants peuvent donner leur avis.",
    "feedback_already_submitted": "✅ Tu as déjà envoyé ton avis pour ce match.",
    "feedback_no_others": "🤔 Aucun autre joueur à signaler dans ce match.",
    "feedback_select_player": "Qui souhaites-tu signaler ? Sélectionne ci-dessous :",
    "feedback_error": "❌ Impossible d'enregistrer l'avis. Réessayer ?",
    "report_thanks": [
        "✅ Signalement envoyé pour **{name}**. Les officiers ont été notifiés.",
    ],
    "officer_alert_title": "⚠️ Rapport Négatif",
    "setup_success_title": "✅ Bot Configuré",
    "setup_footer": "Message de file posté dans le salon.",
    "setup_roles_success": "✅ Rôles de ping mis à jour !",
    "setup_no_auth": "❌ Permission Administrateur ou rôle manager requis.",
    "status_not_setup": "⚠️ Pas encore configuré. Lance d'abord `/drs setup`.",
    "status_title": "Bot de File — Configuration Serveur",
    "lang_set": "✅ Langue définie sur **{lang}**.",
}
