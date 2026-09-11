"""English strings for the DRS bot."""

GEN_EMOJI = "<:Genesis:1519930122566635652>"
ENR_EMOJI = "<:Enrich:1519930167005413466>"
RSE_EMOJI = "<:ModTRSE:1256962175398842399>"
_11_EMOJI = "<:11:1378449282688090184>"
_12_EMOJI = "<:12:1519933592401215570>"

STRINGS: dict = {
    # Pinned Queue Embed Titles & Texts
    "queue_title_drs": "Dark Red Star Queue",
    "queue_title_rs": "Red Star Queue",
    "queue_empty_drs": "*No pilots in the hangar. Hit a level button below to launch!*",
    "queue_empty_rs": "*No pilots in Red Star queue. Select a level below to assemble a fleet!*",
    "queue_title": "⭐ Dark Red Star Queue",
    "queue_empty": "*No pilots in the hangar. Hit a number to launch!*",
    "queue_footer": "Updates every minute · Tap a level to join or leave",
    "queue_legend": f"> -# `Toggle Queue `: 7️⃣–{_12_EMOJI}\n> -# `Exit Queue(s)`: ❌\n> -# `Set Tech     `: {GEN_EMOJI} {ENR_EMOJI} {RSE_EMOJI}\n> -# `Add Time(30m)`: ⏳\n> -# `Duo Start    `: ▶️",

    # Channel Notifications (Broadcasts)
    "notify_joined": [
        "{icon}**{pilot}** joined **{queue}** {count}",
        "{icon}**{pilot}** queued for **{queue}** {count}",
        "{icon}**{pilot}** ready for **{queue}** {count}",
        "{icon}**{pilot}** on deck for **{queue}** {count}",
    ],
    "notify_left": [
        "🚪 {icon}**{pilot}** left **{queue}**",
        "🚪 {icon}**{pilot}** stepped out of **{queue}**",
        "🚪 {icon}**{pilot}** canceled **{queue}**",
    ],
    "notify_left_all": [
        "🚪 {icon}**{pilot}** left all queues ({queues})",
        "🚪 {icon}**{pilot}** exited all queues ({queues})",
    ],
    "notify_qs": [
        "⚡ {icon}{users}**{pilot}** voted Quick Start for **{queue}** {count}",
        "⚡ {icon}{users}**{pilot}** triggered Quick Start for **{queue}** {count}",
        "⚡ {icon}{users}**{pilot}** enabled Quick Start for **{queue}** {count}",
    ],
    "notify_extend": [
        "⏳ {icon}**{pilot}** extended **{queue}** (+30m)",
        "⏳ {icon}**{pilot}** added +30m to **{queue}**",
    ],
    "notify_assist": [
        "🆘 {icon}**{pilot}** requested assistance for **{queue}**",
        "🆘 {icon}**{pilot}** needs wingmen for **{queue}**",
    ],
    "notify_expiry_warning": [
        "⚠️ {icon}<@{user_id}>: spot in **{queue}** expires in **5m** (tap ⏳ to extend)",
        "⚠️ {icon}<@{user_id}>: **{queue}** reservation expires in **5m** (tap ⏳ to extend)",
    ],
    "notify_expired": [
        "⏰ {icon}<@{user_id}> removed from **{queue}** (expired)",
        "⏰ {icon}<@{user_id}> timed out of **{queue}**",
    ],
    "notify_match_formed_title": [
        "⚔️ {queue} Level {level} Fleet Formed! (Match #{match_id})",
        "🚀 Fleet Assembled: {queue}{level}! (Match #{match_id})",
        "💥 Battle Group Ready: {queue}{level}! (Match #{match_id})",
        "🌌 Warp Gate Locked: {queue}{level}! (Match #{match_id})",
        "⭐ Strike Team Deployed: {queue}{level}! (Match #{match_id})",
    ],
    "notify_match_formed_desc": [
        "⏱️ **Formed in:** {duration}\n\n**Pilots On Deck:**\n{roster}\n\n🛰️ *Jump coordinates locked! Check your match thread for loadouts!*",
        "⏱️ **Assembly Time:** {duration}\n\n**Squadron Roster:**\n{roster}\n\n🔥 *Weapons hot, shields energized. Proceed to match thread!*",
        "⏱️ **Queue Duration:** {duration}\n\n**Pilots Ready:**\n{roster}\n\n🚀 *Clear skies and heavy salvage! Report to combat thread!*",
        "⏱️ **Fleet Prep Time:** {duration}\n\n**Strike Wing:**\n{roster}\n\n⚡ *Hyperspace vector aligned. Assemble in match thread!*",
    ],

    # Personal Ephemeral Responses (User Button Clicks)
    "ephemeral_joined": [
        "✅ Locked into **{queue}**! Countdown started (30m). Sit tight or ping wingmen!",
        "✅ Flight clearance granted for **{queue}**! You have 30 minutes before your slot expires.",
        "✅ Cockpit sealed! You are now in line for **{queue}**. Jump prep underway (30m).",
        "✅ Docking clamps released! You're queued for **{queue}** for the next 30 minutes.",
        "✅ Nav-computer programmed for **{queue}**! 30-minute timer ticking.",
        "✅ Standing by on the flight deck for **{queue}** (30m). Good hunting!",
    ],
    "ephemeral_left": [
        "👋 Disengaged from **{queue}**. Hangar bay doors opened.",
        "👋 Withdrawn from **{queue}**. Rest up, pilot!",
        "👋 Stepped down from **{queue}**. Your slot has been freed.",
        "👋 Cancelled your flight plan for **{queue}**.",
        "👋 Stood down from **{queue}**. Catch you on the next run!",
        "👋 Thrusters powered down for **{queue}**.",
    ],
    "ephemeral_left_all": [
        "🚪 Exited all active queues. All flight lines cleared.",
        "🚪 Powered down all ships. You have left all queues.",
        "🚪 Disengaged from all queues. See you in the cantina, pilot!",
        "🚪 All slots relinquished across both DRS & RS.",
        "🚪 Stepped away from the flight board. All active queues cleared.",
    ],
    "ephemeral_extended": [
        "⏳ Extended your queue slot(s) (**{queues}**) by +30 minutes! Warp coils holding.",
        "⏳ +30 minutes added to **{queues}**! Plenty of time to grab some rocket fuel.",
        "⏳ Life support refilled! +30 minutes granted for **{queues}**.",
        "⏳ Berth renewed for **{queues}**! +30m added.",
        "⏳ Thrusters kept warm for **{queues}** — 30 minutes added to the clock!",
    ],
    "ephemeral_qs": [
        "⚡ Quick Start activated for **{queue}**! Ready to launch with 2+ pilots.",
        "⚡ Overdrive engaged on **{queue}**! No wait mode is on.",
        "⚡ Quick Start enabled! As soon as a wingman is ready, we fly!",
        "⚡ Launch bypass enabled for **{queue}**! Fast drop protocol live.",
    ],
    "ephemeral_assist_on": [
        "🆘 Need Assist turned **ON**! Distress beacon lit — other pilots will see you're requesting assistance.",
        "🆘 Need Assist enabled! Squadrons will know you're looking for wingmen to fly escort.",
        "🆘 Beacon active! Your SOS indicator is now visible in the queue.",
    ],
    "ephemeral_assist_off": [
        "✅ Need Assist turned **OFF**! Standing by under standard flight protocol.",
        "✅ Need Assist disabled. SOS beacon deactivated.",
        "✅ Standard flight profile restored — assist flag cleared.",
    ],

    # Legacy & Modal Keys
    "joined": [
        "✅ Locked in for **{queue}**! Clock: {time}\n📋 Queued for: **{levels}**",
        "🚀 **{queue}** confirmed — {time} on the timer.\n📋 Active: **{levels}**",
        "⚡ Ready for **{queue}**! {time} left.\n📋 In queue: **{levels}**",
        "🎯 You're in **{queue}** — {time} until expiry.\n📋 Queued: **{levels}**",
        "💫 **{queue}** — you're in! {time} on the board.\n📋 Active queues: **{levels}**",
    ],
    "left_level": [
        "👋 Left **{queue}**. Still in: **{levels}**",
        "✈️ Ejected from **{queue}**. Remaining: **{levels}**",
        "🚪 Out of **{queue}**. Still queued for: **{levels}**",
    ],
    "left_level_all_gone": [
        "👋 Left **{queue}**. You're queue-free now.",
        "🚪 Stepped out of **{queue}** — all clear.",
        "✈️ Ejected from **{queue}**. No active queues.",
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
        "🔥 **{queue}** match found! Check the thread — it's go time.",
        "⚡ Squad assembled for **{queue}**! Thread is live.",
        "🚀 Match locked for **{queue}**! Head to the thread.",
    ],
    "qs_not_queued": [
        "❓ You're not in any queue. Join a DRS or RS level first.",
        "🤔 Nothing to quick start — get in a queue first!",
    ],
    "qs_multi_queue": [
        "⚠️ You're in multiple queues ({levels}).\nLeave all but one before using ▶️.",
        "❌ Quick start needs a single queue. You're in: {levels}\nLeave the extras first.",
    ],
    "qs_alone": [
        "🧍 You're the only one in **{queue}** right now. Need at least 2!",
        "👀 No one else in **{queue}** yet. Quick start needs a partner.",
    ],
    "qs_already": [
        "⏳ Already signalled ▶️. Waiting for your partner to confirm.",
        "🔔 Quick start pending — ball's in their court!",
    ],
    "qs_confirmed": [
        "🚀 Quick start confirmed! **{queue}** is go. Check the thread!",
        "⚡ Both pilots ready — **{queue}** launching! See the thread.",
    ],
    "qs_sent": [
        "▶️ Quick start sent for **{queue}**! Waiting on your co-pilot.",
        "📡 Signal sent! Partner notified. Standby for confirmation.",
    ],
    "mod_set": [
        "✅ **{mod}** set to level **{level}**. Geared up!",
        "💾 **{mod}** → **{level}** saved. Tech updated!",
        "⚙️ Got it — **{mod}** is now **{level}**.",
    ],
    "mod_prompt": "Your **{mod}** level is currently **{current}**.\nSelect your new level:",
    "mod_not_set": "not set",
    "expiry_warning": [
        "⏰ **{name}** — your **{queue}** slot expires in ~5 minutes! Tap ⏳ to add 30 more.",
        "🚨 **{name}** — {queue} queue timer almost up! Extend now or you'll be dropped.",
        "⌛ **{name}** — 5 minutes left in **{queue}**. Add time if you want to keep your spot!",
    ],
    "expiry_extend_prompt": "⏳ Add 30 min",
    "expiry_extended_ok": "✅ Added 30 minutes to your **{queue}** queue!",
    "expiry_not_yours": "🤔 This extend button isn't for you.",
    "match_proceed": [
        "✅ **{queue}** match complete — please proceed! Good luck pilots 🚀",
        "🚀 **{queue}** squad locked in — head in when ready!",
        "⭐ All pilots confirmed for **{queue}** — fly safe!",
    ],
    "notify_joined_title": "📡 Pilot Incoming — {queue}",
    "notify_qs_title": "▶️ Quick Start — {queue}",
    "match_title": "⭐ {queue} — Match #{match_id}",
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
    "feedback_prompt": "🏁 How was the run?",
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
    "setup_success_title": "✅ Bot Configured",
    "setup_footer": "Queue message posted in the queue channel.",
    "setup_roles_success": "✅ Ping roles updated!",
    "setup_no_auth": "❌ You need Administrator permission or the manager role.",
    "status_not_setup": "⚠️ Not configured yet. Run `/drs setup` first.",
    "status_title": "Queue Bot — Server Config",
    "lang_set": "✅ Language set to **{lang}**.",
}
