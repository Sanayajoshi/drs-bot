"""Hindi strings for the DRS bot."""

GEN_EMOJI = "<:Genesis:1409872792211554365>"
ENR_EMOJI = "<:Enrich:1409872795600424960>"
RSE_EMOJI = "<:ModTRSE:1256962175398842399>"
_11_EMOJI = "<:11:1378449282688090184>"
_12_EMOJI = "<:12:1378449310831607828>"

STRINGS: dict = {
    "queue_title": "⭐ डार्क रेड स्टार कतार",
    "queue_empty": "*हैंगर में कोई पायलट नहीं। नंबर दबाएं!*",
    "queue_footer": "हर मिनट अपडेट · स्तर टैप करें जुड़ने/छोड़ने के लिए",
    "queue_legend": f"> -# `कतार बदलें  `: 7️⃣–{_12_EMOJI}\n> -# `कतार छोड़ें `: ❌\n> -# `टेक सेट करें`: {GEN_EMOJI} {ENR_EMOJI} {RSE_EMOJI}\n> -# `समय(30मिनट) `: ⏳\n> -# `युगल शुरू   `: ▶️",
    "joined": [
        "✅ **DRS{level}** में दर्ज! समय: {time}\n📋 सक्रिय: **{levels}**",
        "🚀 **DRS{level}** पक्का! {time} बचा।\n📋 कतार में: **{levels}**",
    ],
    "left_level": [
        "👋 **DRS{level}** छोड़ा। अभी भी: **{levels}**",
    ],
    "left_level_all_gone": [
        "👋 **DRS{level}** छोड़ा — कोई कतार नहीं।",
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
        "🔥 **DRS{level}** मैच मिला! थ्रेड देखें।",
    ],
    "qs_not_queued": [
        "❓ किसी कतार में नहीं हैं। पहले जुड़ें!",
    ],
    "qs_multi_queue": [
        "⚠️ कई कतारों में हैं ({levels})। ▶️ के लिए एक ही रखें।",
    ],
    "qs_alone": [
        "🧍 **DRS{level}** में आप अकेले हैं। कम से कम 2 चाहिए!",
    ],
    "qs_already": [
        "⏳ ▶️ पहले ही दबाया। दूसरे खिलाड़ी का इंतज़ार।",
    ],
    "qs_confirmed": [
        "🚀 त्वरित शुरुआत पक्की! **DRS{level}** शुरू! थ्रेड देखें।",
    ],
    "qs_sent": [
        "▶️ **DRS{level}** अनुरोध भेजा! पुष्टि का इंतज़ार।",
    ],
    "mod_set": [
        "✅ **{mod}** स्तर **{level}** सेट किया।",
        "💾 **{mod}** → **{level}** सेव!",
    ],
    "mod_prompt": "वर्तमान **{mod}** स्तर: **{current}**\nनया स्तर चुनें:",
    "mod_not_set": "सेट नहीं",
    "notify_left": [
        "👋 **{name}** ने **DRS{level}** कतार छोड़ी।",
        "🚪 **{name}** **DRS{level}** से निकले।",
    ],
    "notify_extend": [
        "⏳ {role}**{name}** ने **DRS{level}** स्लॉट 30 मिनट बढ़ाया।",
        "🕐 {role}**{name}** ने **DRS{level}** रिफ्रेश किया — 30 मिनट और!",
    ],
    "expiry_warning": [
        "⏰ **{name}** — **DRS{level}** स्लॉट ~5 मिनट में समाप्त! ⏳ दबाएं +30 मिनट के लिए।",
        "🚨 **{name}** — DRS{level} टाइमर लगभग खत्म! अभी बढ़ाएं वरना निकाल दिया जाएगा।",
    ],
    "expiry_extend_prompt": "⏳ +30 मिनट",
    "expiry_extended_ok": "✅ **DRS{level}** कतार में 30 मिनट जोड़े!",
    "expiry_not_yours": "🤔 यह बटन आपके लिए नहीं है।",
    "match_proceed": [
        "✅ **DRS{level}** मैच तैयार — कृपया आगे बढ़ें! शुभकामनाएं 🚀",
        "🚀 **DRS{level}** दल तैयार — जब भी तैयार हों, जाएं!",
    ],
    "notify_match_formed": [
        "✅ **DRS{level}** मैच बना — {size}/{size} पायलट। कतार रीसेट!",
    ],
    "notify_joined_title": "📡 पायलट आया — DRS{level}",
    "notify_joined": [
        "**{name}** ने **DRS{level}** में जगह ली! {spots} जगह बची — कौन आ रहा है?",
        "🚀 **{name}** **DRS{level}** के लिए तैयार! {spots} स्लॉट खाली।",
        "⚡ **{name}** DRS{level} कतार में। {spots} और चाहिए!",
        "🎯 **{name}** **DRS{level}** में! {spots} जगह बाकी।",
        "🌟 **{name}** **DRS{level}** में। {spots} और पायलट चाहिए!",
        "📻 नया पायलट! **{name}** ने DRS{level} में जगह ली — {spots} खाली।",
        "💫 **{name}** **DRS{level}** दौड़ना चाहते हैं! {spots} उपलब्ध।",
        "🛸 **{name}** **DRS{level}** के लिए तैयार। {spots} और शुरू!",
        "🔥 **{name}** DRS{level} में। {spots} जगह बची।",
        "⭐ **{name}** **DRS{level}** में। {spots} खाली — जुड़ें!",
    ],
    "notify_qs_title": "▶️ त्वरित शुरुआत — DRS{level}",
    "notify_qs": [
        "**{name}** सिर्फ 2 के साथ **DRS{level}** चलाना चाहते हैं! ▶️ दबाएं।",
        "🚀 **{name}** का **DRS{level}** 2-खिलाड़ी प्रस्ताव! ▶️ दबाएं।",
    ],
    "match_title": "⭐ डार्क रेड स्टार {level} — मैच #{match_id}",
    "match_footer": "शुभकामनाएं — सितारे साथ हों! 🌟",
    "match_warning": [
        "⚡ **{names}** — अंदर जाने से पहले टेक सेट करें!",
    ],
    "match_warning_multi": [
        "⚠️ **{names}** — टेक अधूरा है। शुरू से पहले सेट करें!",
    ],
    "feedback_prompt": "🏁 DRS रन कैसा रहा?",
    "feedback_thanks": [
        "फीडबैक के लिए धन्यवाद! 🌌",
        "नोट कर लिया! 🚀",
        "आपकी राय मिली! ⭐",
    ],
    "feedback_not_participant": "❌ केवल मैच प्रतिभागी ही फीडबैक दे सकते हैं।",
    "feedback_already_submitted": "✅ आपने इस मैच का फीडबैक पहले ही दे दिया है।",
    "feedback_no_others": "🤔 इस मैच में कोई और प्लेयर रिपोर्ट करने के लिए नहीं है।",
    "feedback_select_player": "किसे रिपोर्ट करना चाहते हैं? नीचे से प्लेयर चुनें:",
    "feedback_error": "❌ फीडबैक सेव नहीं हो सका। दोबारा कोशिश करें?",
    "report_thanks": [
        "✅ **{name}** के लिए रिपोर्ट दर्ज की गई। अधिकारियों को सूचित किया गया।",
        "📋 **{name}** को समीक्षा के लिए चिह्नित किया गया।",
    ],
    "officer_alert_title": "⚠️ नकारात्मक रिपोर्ट",
    "setup_success_title": "✅ DRS बॉट कॉन्फ़िगर किया",
    "setup_footer": "कतार संदेश कतार चैनल में पोस्ट किया।",
    "setup_roles_success": "✅ पिंग भूमिकाएं अपडेट हुईं!",
    "setup_no_auth": "❌ व्यवस्थापक अनुमति या मैनेजर भूमिका चाहिए।",
    "status_not_setup": "⚠️ अभी सेट नहीं। `/drs setup` चलाएं।",
    "status_title": "DRS बॉट — सर्वर सेटिंग्स",
    "lang_set": "✅ भाषा **{lang}** पर सेट की।",
}
