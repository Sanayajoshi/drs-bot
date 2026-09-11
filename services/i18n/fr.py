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
        "{icon}**{pilot}** s'est verrouillé dans **{queue}** {count} ! Propulseurs amorcés, en attente des coordonnées de saut.",
        "{icon}Le pilote **{pilot}** s'est enregistré au hangar pour **{queue}** {count} ! Armes parées !",
        "{icon}Signal détecté : **{pilot}** entre en zone de rassemblement pour **{queue}** {count}. Qui saute avec lui ?",
        "{icon}**{pilot}** sur le pont d'envol pour **{queue}** {count}. Bobines supraluminiques en charge !",
        "{icon}Registre de flotte actualisé : **{pilot}** a rejoint **{queue}** {count}. Cap verrouillé !",
        "{icon}**{pilot}** a bouclé son harnais pour **{queue}** {count}. Postes de combat, pilotes !",
    ],
    "notify_left": [
        "🚪 {icon}**{pilot}** s'est désarrimé de **{queue}**. Retour aux quais de la station.",
        "🚪 {icon}**{pilot}** a annulé son ordre de veille pour **{queue}**. Réacteurs coupés.",
        "🚪 {icon}**{pilot}** a interrompu les préparatifs de saut pour **{queue}**. Piste dégagée.",
        "🚪 {icon}Le pilote **{pilot}** a été rappelé au hangar depuis **{queue}**.",
        "🚪 {icon}Plan de vol annulé : **{pilot}** a libéré sa place dans **{queue}**.",
    ],
    "notify_left_all": [
        "🚪 {icon}**{pilot}** a effacé tous ses créneaux ({queues}) et pris sa permission.",
        "🚪 {icon}**{pilot}** a coupé tous ses vaisseaux et quitté toutes les files ({queues}).",
        "🚪 {icon}Plan de vol vierge pour **{pilot}** ({queues}). Bon repos au mess !",
    ],
    "notify_qs": [
        "⚡ {icon}{users}**{pilot}** a activé le **Démarrage Rapide** pour **{queue}** {count} ! Prêt à sauter dès 2+ pilotes !",
        "⚡ {icon}{users}Postcombustion activée ! **{pilot}** ne veut pas attendre dans **{queue}** {count} — paré au saut !",
        "⚡ {icon}{users}**{pilot}** a enclenché le Démarrage Rapide sur **{queue}** {count} ! Faites chauffer les turbines !",
    ],
    "notify_extend": [
        "⏳ {icon}**{pilot}** a refait le plein : +30 minutes ajoutées à son créneau **{queue}** !",
        "⏳ {icon}**{pilot}** a repris un café de l'espace — reste amarré dans **{queue}** pour 30m de plus !",
        "⏳ {icon}Survie prolongée ! **{pilot}** a ajouté 30 minutes à son billet pour **{queue}**.",
    ],
    "notify_assist": [
        "🆘 {icon}Le pilote **{pilot}** a tiré une fusée de détresse ! Recherche ailiers en renfort !",
        "🆘 {icon}**{pilot}** demande escorte et assistance de flotte ! Vétérans, aux commandes !",
        "🆘 {icon}Comms de flotte : **{pilot}** a activé **Need Assist** ! Quels commandants sont prêts à escorter ?",
    ],
    "notify_expiry_warning": [
        "⚠️ {icon}<@{user_id}> (**{pilot}**), votre fenêtre de saut pour **{queue}** expire dans **5 minutes** ! Cliquez sur ⏳ pour prolonger !",
        "⚠️ {icon}Voyants d'alerte allumés : la place de <@{user_id}> (**{pilot}**) dans **{queue}** expire dans **5 minutes** ! Tapez ⏳ !",
    ],
    "notify_expired": [
        "⏰ {icon}<@{user_id}> (**{pilot}**) est sorti de portée radar — retiré de **{queue}** pour inactivité.",
        "⏰ {icon}Créneau de hangar expiré pour <@{user_id}> (**{pilot}**) dans **{queue}**. Place libérée !",
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
