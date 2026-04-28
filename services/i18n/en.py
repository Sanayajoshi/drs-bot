"""English strings for the DRS bot."""

GEN_EMOJI = "<:Genesis:1409872792211554365>"
ENR_EMOJI = "<:Enrich:1409872795600424960>"
RSE_EMOJI = "<:ModTRSE:1256962175398842399>"
_11_EMOJI = "<:11:1378449282688090184>"
_12_EMOJI = "<:12:1378449310831607828>"

STRINGS: dict = {
    "queue_title": "⭐ Dark Red Star Queue",
    "queue_empty": "*No pilots in the hangar. Hit a number to launch!*",
    "queue_footer": "Updates every minute · Tap a level to join or leave",
    "queue_legend": f"> -# `Toggle Queue `: 7️⃣–{_12_EMOJI}\n> -# `Exit Queue(s)`: ❌\n> -# `Set Tech     `: {GEN_EMOJI} {ENR_EMOJI} {RSE_EMOJI}\n> -# `Add Time(30m)`: ⏳\n> -# `Duo Start    `: ▶️",
    "joined": [
        "✅ Locked in for **DRS{level}**! Clock: {time}\n📋 Queued for: **{levels}**",
        "🚀 **DRS{level}** confirmed — {time} on the timer.\n📋 Active: **{levels}**",
        "⚡ Ready for **DRS{level}**! {time} left.\n📋 In queue: **{levels}**",
        "🎯 You're in **DRS{level}** — {time} until expiry.\n📋 Queued: **{levels}**",
        "💫 **DRS{level}** — you're in! {time} on the board.\n📋 Active queues: **{levels}**",
    ],
    "left_level": [
        "👋 Left **DRS{level}**. Still in: **{levels}**",
        "✈️ Ejected from **DRS{level}**. Remaining: **{levels}**",
        "🚪 Out of **DRS{level}**. Still queued for: **{levels}**",
    ],
    "left_level_all_gone": [
        "👋 Left **DRS{level}**. You're queue-free now.",
        "🚪 Stepped out of **DRS{level}** — all clear.",
        "✈️ Ejected from **DRS{level}**. No active queues.",
    ],
    "left_all": [
        "🚪 Cleared out of all queues ({levels}). See you next run!",
        "👋 Gone from {levels}. Queue's clean.",
        "✈️ Ejected from {levels}. Ready when you are!",
    ],
    "not_in_queue": [
        "🤔 You're not in any queue right now.",
        "❓ No active queues found for you.",
        "🛸 You're not queued anywhere yet.",
    ],
    "extended": [
        "⏳ Extended all queues by **{mins} min** ({levels}). Clock reset!",
        "🕐 +{mins} minutes added to {levels}. You've got time!",
        "⌛ Your slots in {levels} topped up by **{mins} min**.",
    ],
    "match_formed": [
        "🔥 **DRS{level}** match found! Check the thread — it's go time.",
        "⚡ Squad assembled for **DRS{level}**! Thread is live.",
        "🚀 Match locked for **DRS{level}**! Head to the thread.",
    ],
    "qs_not_queued": [
        "❓ You're not in any queue. Join a DRS level first.",
        "🤔 Nothing to quick start — get in a queue first!",
    ],
    "qs_multi_queue": [
        "⚠️ You're in multiple queues ({levels}).\nLeave all but one before using ▶️.",
        "❌ Quick start needs a single queue. You're in: {levels}\nLeave the extras first.",
    ],
    "qs_alone": [
        "🧍 You're the only one in **DRS{level}** right now. Need at least 2!",
        "👀 No one else in **DRS{level}** yet. Quick start needs a partner.",
    ],
    "qs_already": [
        "⏳ Already signalled ▶️. Waiting for your partner to confirm.",
        "🔔 Quick start pending — ball's in their court!",
    ],
    "qs_confirmed": [
        "🚀 Quick start confirmed! **DRS{level}** is go. Check the thread!",
        "⚡ Both pilots ready — **DRS{level}** launching! See the thread.",
    ],
    "qs_sent": [
        "▶️ Quick start sent for **DRS{level}**! Waiting on your co-pilot.",
        "📡 Signal sent! Partner notified. Standby for confirmation.",
    ],
    "mod_set": [
        "✅ **{mod}** set to level **{level}**. Geared up!",
        "💾 **{mod}** → **{level}** saved. Tech updated!",
        "⚙️ Got it — **{mod}** is now **{level}**.",
    ],
    "mod_prompt": "Your **{mod}** level is currently **{current}**.\nSelect your new level:",
    "mod_not_set": "not set",
    "notify_left": [
        "👋 **{name}** left the **DRS{level}** queue.",
        "🚪 **{name}** stepped out of **DRS{level}**.",
        "✈️ **{name}** ejected from **DRS{level}** queue.",
    ],
    "notify_extend": [
        "⏳ {role}**{name}** extended their **DRS{level}** slot by 30 minutes.",
        "🕐 {role}**{name}** topped up **DRS{level}** — back in for another 30 min!",
        "⌛ {role}**{name}** refreshed their **DRS{level}** timer. Queue still alive!",
    ],
    "expiry_warning": [
        "⏰ **{name}** — your **DRS{level}** slot expires in ~5 minutes! Tap ⏳ to add 30 more.",
        "🚨 **{name}** — DRS{level} queue timer almost up! Extend now or you'll be dropped.",
        "⌛ **{name}** — 5 minutes left in **DRS{level}**. Add time if you want to keep your spot!",
    ],
    "expiry_extend_prompt": "⏳ Add 30 min",
    "expiry_extended_ok": "✅ Added 30 minutes to your **DRS{level}** queue!",
    "expiry_not_yours": "🤔 This extend button isn't for you.",
    "match_proceed": [
        "✅ **DRS{level}** match complete — please proceed! Good luck pilots 🚀",
        "🚀 **DRS{level}** squad locked in — head in when ready!",
        "⭐ All pilots confirmed for **DRS{level}** — fly safe!",
    ],
    "notify_match_formed": [
        "✅ **DRS{level}** match formed — {size}/{size} pilots locked in. Queue reset.",
        "🚀 **DRS{level}** is a go — full squad assembled ({size}/{size})!",
        "⭐ **DRS{level}** match complete — {size}/{size}. Good luck in there!",
    ],
    "notify_joined_title": "📡 Pilot Incoming — DRS{level}",
    "notify_joined": [
        "**{name}** just queued for **DRS{level}**! {spots} spot(s) left — who's joining?",
        "🚀 **{name}** is locked in for **DRS{level}**. {spots} slot(s) open!",
        "⚡ **{name}** entered DRS{level}. {spots} more needed — don't miss out!",
        "🎯 **{name}** ready for **DRS{level}**! {spots} spot(s) left.",
        "🌟 **{name}** joined **DRS{level}**. Room for {spots} more pilot(s)!",
        "📻 Incoming pilot! **{name}** queued for **DRS{level}** — {spots} available.",
        "💫 **{name}** wants to run **DRS{level}**! {spots} slot(s) up for grabs.",
        "🛸 **{name}** registered for **DRS{level}**. {spots} more to launch!",
        "🔥 **{name}** ready to burn a **DRS{level}**! {spots} spot(s) left.",
        "⭐ **{name}** in queue for **DRS{level}**. {spots} open — jump in!",
    ],
    "notify_qs_title": "▶️ Quick Start — DRS{level}",
    "notify_qs": [
        "**{name}** wants to run **DRS{level}** with just 2! Click ▶️ on the queue to confirm.",
        "🚀 **{name}** is itching to go on **DRS{level}** — 2-player run proposed! Hit ▶️.",
        "⚡ 2-pilot run requested! **{name}** wants to start **DRS{level}** now. Tap ▶️!",
    ],
    "match_title": "⭐ Dark Red Star {level} — Match #{match_id}",
    "match_footer": "Good luck — may the stars align 🌟",
    "match_warning": [
        "⚡ **{names}** — sort your tech before warping in!",
        "⚠️ **{names}** — update your mods before launch!",
        "🔧 **{names}** — get your tech sorted, then we fly!",
    ],
    "match_warning_multi": [
        "⚡ **{names}** — sort your tech before warping in!",
        "⚠️ Some pilots are missing tech. **{names}** — update before launch!",
    ],
    "feedback_prompt": "🏁 How was the DRS run?",
    "feedback_thanks": [
        "Thanks for the feedback! Keeping the galaxy safe. 🌌",
        "Noted! Every run counts. 🚀",
        "Feedback received — appreciate it! ⭐",
    ],
    "feedback_not_participant": "❌ Only match participants can submit feedback.",
    "feedback_already_submitted": "✅ You've already submitted feedback for this match.",
    "feedback_no_others": "🤔 No other players to report in this match.",
    "feedback_select_player": "Who do you want to report? Select a player below:",
    "feedback_error": "❌ Couldn't record your feedback. Try again?",
    "report_thanks": [
        "✅ Report submitted for **{name}**. Officers have been notified.",
        "📋 Got it — **{name}** has been flagged for review.",
        "🚨 Report filed for **{name}**. The officer team will look into it.",
    ],
    "officer_alert_title": "⚠️ Negative Run Report",
    "setup_success_title": "✅ DRS Bot Configured",
    "setup_footer": "Queue message posted in the queue channel.",
    "setup_roles_success": "✅ Ping roles updated!",
    "setup_no_auth": "❌ You need Administrator permission or the manager role.",
    "status_not_setup": "⚠️ Not configured yet. Run `/drs setup` first.",
    "status_title": "DRS Bot — Server Config",
    "lang_set": "✅ Language set to **{lang}**.",
}
