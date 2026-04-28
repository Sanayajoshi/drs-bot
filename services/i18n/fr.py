"""French strings for the DRS bot."""

GEN_EMOJI = "<:Genesis:1409872792211554365>"
ENR_EMOJI = "<:Enrich:1409872795600424960>"
RSE_EMOJI = "<:ModTRSE:1256962175398842399>"
_11_EMOJI = "<:11:1378449282688090184>"
_12_EMOJI = "<:12:1378449310831607828>"

STRINGS: dict = {
    "queue_title": "⭐ File d'attente Étoile Rouge Sombre",
    "queue_empty": "*Aucun pilote dans le hangar. Appuie sur un numéro pour décoller !*",
    "queue_footer": "Mise à jour chaque minute · Appuie sur un niveau pour rejoindre ou quitter",
    "queue_legend": f"> -# `Basculer File  `: 7️⃣–{_12_EMOJI}\n> -# `Quitter File(s)`: ❌\n> -# `Config Tech    `: {GEN_EMOJI} {ENR_EMOJI} {RSE_EMOJI}\n> -# `Ajouter(30min) `: ⏳\n> -# `Duo Start      `: ▶️",
    "joined": [
        "✅ Inscrit pour **DRS{level}** ! Temps : {time}\n📋 Files actives : **{levels}**",
        "🚀 **DRS{level}** confirmé — {time} au chrono.\n📋 Actif : **{levels}**",
        "⚡ Prêt pour **DRS{level}** ! {time} restant.\n📋 En file : **{levels}**",
        "🎯 Tu es dans **DRS{level}** — {time} avant expiration.\n📋 Files : **{levels}**",
        "💫 **DRS{level}** — c'est parti ! {time} au compteur.\n📋 Files actives : **{levels}**",
    ],
    "left_level": [
        "👋 Quitté **DRS{level}**. Encore dans : **{levels}**",
        "✈️ Éjecté de **DRS{level}**. Restant : **{levels}**",
        "🚪 Sorti de **DRS{level}**. Toujours en file pour : **{levels}**",
    ],
    "left_level_all_gone": [
        "👋 Quitté **DRS{level}**. Plus aucune file active.",
        "🚪 Sorti de **DRS{level}** — tout est libre.",
        "✈️ Éjecté de **DRS{level}**. Aucune file active.",
    ],
    "left_all": [
        "🚪 Sorti de toutes les files ({levels}). À la prochaine !",
        "👋 Plus dans {levels}. File propre.",
        "✈️ Éjecté de {levels}. Prêt quand tu veux !",
    ],
    "not_in_queue": [
        "🤔 Tu n'es dans aucune file pour le moment.",
        "❓ Aucune file active trouvée.",
        "🛸 Tu n'es encore inscrit nulle part.",
    ],
    "extended": [
        "⏳ Toutes les files prolongées de **{mins} min** ({levels}). Chrono réinitialisé !",
        "🕐 +{mins} minutes ajoutées à {levels}. Tu as le temps !",
        "⌛ Tes places dans {levels} rechargées de **{mins} min**.",
    ],
    "match_formed": [
        "🔥 Match **DRS{level}** trouvé ! Consulte le fil — c'est l'heure.",
        "⚡ Équipe formée pour **DRS{level}** ! Le fil est en direct.",
        "🚀 Match confirmé pour **DRS{level}** ! Direction le fil.",
    ],
    "qs_not_queued": [
        "❓ Tu n'es dans aucune file. Rejoins un niveau DRS d'abord.",
        "🤔 Rien à démarrer rapidement — inscris-toi d'abord !",
    ],
    "qs_multi_queue": [
        "⚠️ Tu es dans plusieurs files ({levels}).\nQuitte toutes sauf une avant d'utiliser ▶️.",
        "❌ Le démarrage rapide nécessite une seule file. Tu es dans : {levels}\nQuitte les autres d'abord.",
    ],
    "qs_alone": [
        "🧍 Tu es le seul dans **DRS{level}** pour l'instant. Il faut au moins 2 !",
        "👀 Personne d'autre dans **DRS{level}**. Le démarrage rapide nécessite un partenaire.",
    ],
    "qs_already": [
        "⏳ Tu as déjà signalé ▶️. En attente de confirmation de ton partenaire.",
        "🔔 Démarrage rapide en attente — la balle est dans leur camp !",
    ],
    "qs_confirmed": [
        "🚀 Démarrage rapide confirmé ! **DRS{level}** c'est parti. Consulte le fil !",
        "⚡ Les deux pilotes sont prêts — **DRS{level}** décolle ! Voir le fil.",
    ],
    "qs_sent": [
        "▶️ Démarrage rapide envoyé pour **DRS{level}** ! En attente de ton co-pilote.",
        "📡 Signal envoyé ! Partenaire notifié. En attente de confirmation.",
    ],
    "mod_set": [
        "✅ **{mod}** défini au niveau **{level}**. Équipé !",
        "💾 **{mod}** → **{level}** sauvegardé. Tech mis à jour !",
        "⚙️ Compris — **{mod}** est maintenant **{level}**.",
    ],
    "mod_prompt": "Ton niveau **{mod}** actuel est **{current}**.\nSélectionne ton nouveau niveau :",
    "mod_not_set": "non défini",
    "notify_left": [
        "👋 **{name}** a quitté la file **DRS{level}**.",
        "🚪 **{name}** est sorti de **DRS{level}**.",
        "✈️ **{name}** éjecté de la file **DRS{level}**.",
    ],
    "notify_extend": [
        "⏳ {role}**{name}** a prolongé sa place en **DRS{level}** de 30 minutes.",
        "🕐 {role}**{name}** a rechargé **DRS{level}** — encore 30 min !",
        "⌛ {role}**{name}** a rafraîchi son timer **DRS{level}**. File toujours active !",
    ],
    "expiry_warning": [
        "⏰ **{name}** — ta place en **DRS{level}** expire dans ~5 minutes ! Appuie sur ⏳ pour ajouter 30 min.",
        "🚨 **{name}** — le timer DRS{level} est presque écoulé ! Prolonge maintenant ou tu seras retiré.",
        "⌛ **{name}** — 5 minutes restantes en **DRS{level}**. Ajoute du temps si tu veux garder ta place !",
    ],
    "expiry_extend_prompt": "⏳ Ajouter 30 min",
    "expiry_extended_ok": "✅ 30 minutes ajoutées à ta file **DRS{level}** !",
    "expiry_not_yours": "🤔 Ce bouton n'est pas pour toi.",
    "match_proceed": [
        "✅ Match **DRS{level}** prêt — en avant, pilotes ! 🚀",
        "🚀 Escouade **DRS{level}** au complet — partez quand vous êtes prêts !",
        "⭐ Tous les pilotes confirmés pour **DRS{level}** — bon vol !",
    ],
    "notify_match_formed": [
        "✅ Match **DRS{level}** formé — {size}/{size} pilotes confirmés. File réinitialisée.",
        "🚀 **DRS{level}** c'est parti — équipe complète ({size}/{size}) !",
        "⭐ Match **DRS{level}** complet — {size}/{size}. Bonne chance là-dedans !",
    ],
    "notify_joined_title": "📡 Pilote entrant — DRS{level}",
    "notify_joined": [
        "**{name}** vient de rejoindre **DRS{level}** ! {spots} place(s) restante(s) — qui embarque ?",
        "🚀 **{name}** est inscrit pour **DRS{level}**. {spots} slot(s) disponible(s) !",
        "⚡ **{name}** a rejoint DRS{level}. {spots} de plus nécessaires — ne rate pas ça !",
        "🎯 **{name}** prêt pour **DRS{level}** ! {spots} place(s) libre(s).",
        "🌟 **{name}** dans **DRS{level}**. De la place pour {spots} pilote(s) de plus !",
        "📻 Pilote entrant ! **{name}** en file pour **DRS{level}** — {spots} disponible(s).",
        "💫 **{name}** veut courir **DRS{level}** ! {spots} slot(s) à prendre.",
        "🛸 **{name}** inscrit pour **DRS{level}**. {spots} de plus pour le lancement !",
        "🔥 **{name}** prêt à brûler **DRS{level}** ! {spots} place(s) restante(s).",
        "⭐ **{name}** en file pour **DRS{level}**. {spots} libre(s) — rejoins !",
    ],
    "notify_qs_title": "▶️ Démarrage Rapide — DRS{level}",
    "notify_qs": [
        "**{name}** veut courir **DRS{level}** à seulement 2 ! Clique ▶️ sur la file pour confirmer.",
        "🚀 **{name}** est impatient pour **DRS{level}** — run à 2 proposé ! Appuie sur ▶️.",
        "⚡ Run à 2 pilotes ! **{name}** veut démarrer **DRS{level}** maintenant. Appuie sur ▶️ !",
    ],
    "match_title": "⭐ Étoile Rouge Sombre {level} — Match #{match_id}",
    "match_footer": "Bonne chance — que les étoiles s'alignent 🌟",
    "match_warning": [
        "⚡ **{names}** — configure ta tech avant de te téléporter !",
        "⚠️ **{names}** — mets à jour tes mods avant le lancement !",
        "🔧 **{names}** — règle ta tech, ensuite on vole !",
    ],
    "match_warning_multi": [
        "⚡ **{names}** — configurez votre tech avant de vous téléporter !",
        "⚠️ Des pilotes manquent de tech. **{names}** — mise à jour avant le lancement !",
    ],
    "feedback_prompt": "🏁 Comment s'est passé le run DRS ?",
    "feedback_thanks": [
        "Merci pour ton retour ! On garde la galaxie sûre. 🌌",
        "Noté ! Chaque run compte. 🚀",
        "Retour reçu — merci ! ⭐",
    ],
    "feedback_not_participant": "❌ Seuls les participants du match peuvent soumettre un retour.",
    "feedback_already_submitted": "✅ Tu as déjà soumis un retour pour ce match.",
    "feedback_no_others": "🤔 Aucun autre joueur à signaler dans ce match.",
    "feedback_select_player": "Qui veux-tu signaler ? Sélectionne un joueur ci-dessous :",
    "feedback_error": "❌ Impossible d'enregistrer ton retour. Réessayer ?",
    "report_thanks": [
        "✅ Signalement soumis pour **{name}**. Les officiers ont été notifiés.",
        "📋 Compris — **{name}** a été signalé pour examen.",
        "🚨 Signalement déposé pour **{name}**. L'équipe des officiers va examiner ça.",
    ],
    "officer_alert_title": "⚠️ Rapport de Run Négatif",
    "setup_success_title": "✅ DRS Bot Configuré",
    "setup_footer": "Message de file posté dans le canal de file.",
    "setup_roles_success": "✅ Rôles de ping mis à jour !",
    "setup_no_auth": "❌ Tu as besoin de la permission Administrateur ou du rôle gestionnaire.",
    "status_not_setup": "⚠️ Pas encore configuré. Lance `/drs setup` d'abord.",
    "status_title": "DRS Bot — Config Serveur",
    "lang_set": "✅ Langue définie sur **{lang}**.",
}
