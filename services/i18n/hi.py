"""Hindi strings for the DRS bot."""

GEN_EMOJI = "<:Genesis:1519930122566635652>"
ENR_EMOJI = "<:Enrich:1519930167005413466>"
RSE_EMOJI = "<:ModTRSE:1256962175398842399>"
_11_EMOJI = "<:11:1378449282688090184>"
_12_EMOJI = "<:12:1519933592401215570>"

STRINGS: dict = {
    # Pinned Queue Embed Titles & Texts
    "queue_title_drs": "डार्क रेड स्टार कतार",
    "queue_title_rs": "रेड स्टार कतार",
    "queue_empty_drs": "*हैंगर में कोई पायलट नहीं है। उड़ान भरने के लिए नीचे स्तर चुनें!*",
    "queue_empty_rs": "*रेड स्टार कतार में कोई पायलट नहीं है। बेड़ा तैयार करने के लिए नीचे स्तर चुनें!*",
    "queue_title": "⭐ डार्क रेड स्टार कतार",
    "queue_empty": "*हैंगर में कोई पायलट नहीं। नंबर दबाएं!*",
    "queue_footer": "हर मिनट अपडेट · स्तर टैप करें जुड़ने/छोड़ने के लिए",
    "queue_legend": f"> -# `कतार बदलें  `: 7️⃣–{_12_EMOJI}\n> -# `कतार छोड़ें `: ❌\n> -# `टेक सेट करें`: {GEN_EMOJI} {ENR_EMOJI} {RSE_EMOJI}\n> -# `समय(30मिनट) `: ⏳\n> -# `युगल शुरू   `: ▶️",

    # Channel Notifications (Broadcasts)
    "notify_joined": [
        "{icon}**{pilot}** **{queue}** {count} में शामिल हुए",
        "{icon}**{pilot}** **{queue}** {count} के लिए तैयार हैं",
    ],
    "notify_left": [
        "🚪 {icon}**{pilot}** ने **{queue}** छोड़ दी",
    ],
    "notify_left_all": [
        "🚪 {icon}**{pilot}** सभी कतारों ({queues}) से बाहर निकले",
    ],
    "notify_qs": [
        "⚡ {icon}{users}**{pilot}** ने **{queue}** {count} के लिए त्वरित शुरुआत सक्रिय की",
    ],
    "notify_extend": [
        "⏳ {icon}**{pilot}** ने **{queue}** का समय बढ़ाया (+30 मिनट)",
    ],
    "notify_assist": [
        "🆘 {icon}**{pilot}** ने **{queue}** के लिए सहायता मांगी",
    ],
    "notify_expiry_warning": [
        "⚠️ {icon}<@{user_id}>: **{queue}** स्लॉट **5 मिनट** में समाप्त होगा (⏳ से बढ़ाएं)",
    ],
    "notify_expired": [
        "⏰ {icon}<@{user_id}> समय समाप्त होने पर **{queue}** से हटा दिए गए",
    ],
    "notify_match_formed_title": [
        "⚔️ {queue} स्तर {level} का बेड़ा तैयार! (मैच #{match_id})",
        "🚀 बेड़ा इकट्ठा हुआ: {queue}{level}! (मैच #{match_id})",
        "💥 युद्ध समूह तैयार: {queue}{level}! (मैच #{match_id})",
    ],
    "notify_match_formed_desc": [
        "⏱️ **कतार बनने का समय:** {duration}\n\n**तैयार पायलट:**\n{roster}\n\n🛰️ *छलांग के निर्देशांक तय! मैच थ्रेड में चेक करें!*",
        "⏱️ **तैयारी का समय:** {duration}\n\n**स्क्वाड्रन सूची:**\n{roster}\n\n🔥 *हथियार तैयार, शील्ड चालू। मैच थ्रेड में चलें!*",
    ],

    # Personal Ephemeral Responses
    "ephemeral_joined": [
        "✅ **{queue}** में शामिल हुए! 30 मिनट का समय शुरू। साथी पायलटों का इंतज़ार करें!",
        "✅ **{queue}** के लिए उड़ान की अनुमति मिली (30 मिनट)।",
        "✅ कॉकपिट बंद! आप **{queue}** की कतार में हैं (30 मिनट)।",
    ],
    "ephemeral_left": [
        "👋 **{queue}** से बाहर निकले। हैंगर के दरवाजे खुल गए।",
        "👋 **{queue}** छोड़ा। आराम करें, पायलट!",
    ],
    "ephemeral_left_all": [
        "🚪 सभी सक्रिय कतारें छोड़ीं। उड़ान मार्ग साफ।",
        "🚪 सभी जहाजों को बंद किया। आप सभी कतारों से बाहर हैं।",
    ],
    "ephemeral_extended": [
        "⏳ कतार समय (**{queues}**) +30 मिनट बढ़ाया गया!",
        "⏳ +30 मिनट **{queues}** में जोड़े गए! ईंधन भरने का पूरा समय है।",
    ],
    "ephemeral_qs": [
        "⚡ **{queue}** के लिए त्वरित शुरुआत चालू! 2+ पायलट होते ही उड़ान!",
    ],
    "ephemeral_assist_on": [
        "🆘 सहायता अनुरोध चालू (**ON**)! अन्य पायलटों को आपका सिग्नल दिखेगा।",
    ],
    "ephemeral_assist_off": [
        "✅ सहायता अनुरोध बंद (**OFF**)। सामान्य उड़ान मोड पर वापस।",
    ],

    # Legacy & Modals
    "joined": [
        "✅ **{queue}** में दर्ज! समय: {time}\n📋 सक्रिय: **{levels}**",
        "🚀 **{queue}** पक्का! {time} बचा।\n📋 कतार में: **{levels}**",
    ],
    "left_level": [
        "👋 **{queue}** छोड़ा। अभी भी: **{levels}**",
    ],
    "left_level_all_gone": [
        "👋 **{queue}** छोड़ा — कोई कतार नहीं।",
    ],
    "left_all": [
        "🚪 सभी कतारें छोड़ी ({levels})। फिर मिलेंगे!",
    ],
    "not_in_queue": [
        "🤔 आप किसी कतार में नहीं हैं।",
    ],
    "extended": [
        "⏳ {levels} की कतार **{mins} मिनट** बढ़ाई!",
    ],
    "match_formed": [
        "🔥 **{queue}** मैच मिला! थ्रेड देखें।",
    ],
    "qs_not_queued": [
        "❓ किसी कतार में नहीं हैं। पहले जुड़ें!",
    ],
    "qs_multi_queue": [
        "⚠️ कई कतारों में हैं ({levels})। ▶️ के लिए एक ही रखें।",
    ],
    "qs_alone": [
        "🧍 **{queue}** में आप अकेले हैं। कम से कम 2 चाहिए!",
    ],
    "qs_already": [
        "⏳ ▶️ पहले ही दबाया। दूसरे खिलाड़ी का इंतज़ार।",
    ],
    "qs_confirmed": [
        "🚀 त्वरित शुरुआत पक्की! **{queue}** शुरू! थ्रेड देखें।",
    ],
    "qs_sent": [
        "▶️ **{queue}** अनुरोध भेजा! पुष्टि का इंतज़ार।",
    ],
    "mod_set": [
        "✅ **{mod}** स्तर **{level}** सेट किया।",
    ],
    "mod_prompt": "वर्तमान **{mod}** स्तर: **{current}**\nनया स्तर चुनें:",
    "mod_not_set": "सेट नहीं",
    "expiry_warning": [
        "⏰ **{name}** — **{queue}** में स्लॉट ~5 मिनट में समाप्त! ⏳ दबाएं।",
    ],
    "expiry_extend_prompt": "⏳ +30 मिनट",
    "expiry_extended_ok": "✅ **{queue}** कतार में 30 मिनट जोड़े!",
    "expiry_not_yours": "🤔 यह बटन आपके लिए नहीं है।",
    "match_proceed": [
        "✅ **{queue}** मैच पूरा — आगे बढ़ें पायलट! 🚀",
    ],
    "match_title": "⭐ {queue} — मैच #{match_id}",
    "match_footer": "शुभकामनाएं — सितारे आपके साथ हों 🌟",
    "match_warning": [
        "⚡ **{names}** — उड़ान से पहले अपनी तकनीक सेट करें!",
    ],
    "match_warning_multi": [
        "⚡ **{names}** — उड़ान से पहले अपनी तकनीक सेट करें!",
    ],
    "feedback_prompt": "🏁 रन कैसा रहा?",
    "feedback_thanks": [
        "प्रतिक्रिया के लिए धन्यवाद! 🌌",
    ],
    "feedback_not_participant": "❌ केवल मैच के प्रतिभागी ही प्रतिक्रिया दे सकते हैं।",
    "feedback_already_submitted": "✅ आपने पहले ही प्रतिक्रिया दे दी है।",
    "feedback_no_others": "🤔 रिपोर्ट करने के लिए अन्य खिलाड़ी नहीं हैं।",
    "feedback_select_player": "किसकी रिपोर्ट करना चाहते हैं? नीचे चुनें:",
    "feedback_error": "❌ प्रतिक्रिया दर्ज नहीं हो सकी। पुनः प्रयास करें?",
    "report_thanks": [
        "✅ **{name}** की रिपोर्ट दर्ज हुई। अधिकारियों को सूचित किया गया।",
    ],
    "officer_alert_title": "⚠️ नकारात्मक रिपोर्ट",
    "setup_success_title": "✅ बॉट कॉन्फ़िगर हो गया",
    "setup_footer": "कतार संदेश चैनल में पोस्ट किया गया।",
    "setup_roles_success": "✅ पिंग भूमिकाएं अपडेट हुईं!",
    "setup_no_auth": "❌ आपको व्यवस्थापक अनुमति या प्रबंधक भूमिका चाहिए।",
    "status_not_setup": "⚠️ अभी कॉन्फ़िगर नहीं है। पहले `/drs setup` चलाएं।",
    "status_title": "कतार बॉट — सर्वर कॉन्फ़िग",
    "lang_set": "✅ भाषा **{lang}** सेट की गई।",
}
