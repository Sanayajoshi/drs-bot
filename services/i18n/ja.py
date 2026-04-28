"""Japanese strings for the DRS bot."""

GEN_EMOJI = "<:Genesis:1409872792211554365>"
ENR_EMOJI = "<:Enrich:1409872795600424960>"
RSE_EMOJI = "<:ModTRSE:1256962175398842399>"
_11_EMOJI = "<:11:1378449282688090184>"
_12_EMOJI = "<:12:1378449310831607828>"

STRINGS: dict = {
    "queue_title": "⭐ ダークレッドスター キュー",
    "queue_empty": "*パイロット募集中。番号を押して参加しよう！*",
    "queue_footer": "毎分更新 · 番号でキュー参加/退出",
    "queue_legend": f"> -# `キュー切替`: 7️⃣–{_12_EMOJI}\n> -# `キュー退出`: ❌\n> -# `テック設定   `: {GEN_EMOJI} {ENR_EMOJI} {RSE_EMOJI}\n> -# `時間追加(30分)`: ⏳\n> -# `デュオ開始   `: ▶️",
    "joined": [
        "✅ **DRS{level}** に参加！残り時間: {time}\n📋 参加中: **{levels}**",
        "🚀 **DRS{level}** 確定！タイマー: {time}。\n📋 キュー: **{levels}**",
        "⚡ **DRS{level}** 登録完了！{time} 残り。\n📋 参加中: **{levels}**",
    ],
    "left_level": [
        "👋 **DRS{level}** を退出。残り: **{levels}**",
        "🚪 **DRS{level}** 離脱。残りキュー: **{levels}**",
    ],
    "left_level_all_gone": [
        "👋 **DRS{level}** 退出 — キュークリア。",
        "🚪 **DRS{level}** を退出。全キュー離脱。",
    ],
    "left_all": [
        "🚪 {levels} から全て退出しました。またね！",
        "👋 {levels} を離れました。次回また！",
    ],
    "not_in_queue": [
        "🤔 現在どのキューにも参加していません。",
        "❓ アクティブなキューが見つかりません。",
    ],
    "extended": [
        "⏳ {levels} を **{mins}分** 延長しました！",
        "🕐 {levels} に +{mins}分 追加。",
    ],
    "match_formed": [
        "🔥 **DRS{level}** マッチ成立！スレッドを確認してください。",
        "⚡ **DRS{level}** 開始！スレッドへどうぞ。",
    ],
    "qs_not_queued": [
        "❓ キューに参加していません。まず参加してください。",
    ],
    "qs_multi_queue": [
        "⚠️ 複数キューに参加中です（{levels}）。▶️ には1つのキューのみ必要です。",
    ],
    "qs_alone": [
        "🧍 **DRS{level}** に他のプレイヤーがいません。最低2人必要です！",
    ],
    "qs_already": [
        "⏳ すでに ▶️ を押しました。相手の確認を待っています。",
    ],
    "qs_confirmed": [
        "🚀 クイックスタート確定！**DRS{level}** 発進！スレッドを確認してください。",
    ],
    "qs_sent": [
        "▶️ **DRS{level}** のクイックスタートリクエストを送信しました！確認待ち。",
    ],
    "mod_set": [
        "✅ **{mod}** レベルを **{level}** に設定しました！",
        "💾 **{mod}** → **{level}** 保存完了！",
    ],
    "mod_prompt": "現在の **{mod}** レベル: **{current}**\n新しいレベルを選択してください:",
    "mod_not_set": "未設定",
    "notify_left": [
        "👋 **{name}** が **DRS{level}** キューを退出しました。",
        "🚪 **{name}** が **DRS{level}** から離脱しました。",
    ],
    "notify_extend": [
        "⏳ {role}**{name}** が **DRS{level}** のスロットを30分延長しました。",
        "🕐 {role}**{name}** が **DRS{level}** をリフレッシュ — あと30分！",
    ],
    "expiry_warning": [
        "⏰ **{name}** — **DRS{level}** のスロットがあと5分で期限切れです！⏳ で延長してください。",
        "🚨 **{name}** — DRS{level} のタイマーが切れそうです！今すぐ延長しましょう。",
    ],
    "expiry_extend_prompt": "⏳ 30分追加",
    "expiry_extended_ok": "✅ **DRS{level}** キューに30分追加しました！",
    "expiry_not_yours": "🤔 このボタンはあなた用ではありません。",
    "match_proceed": [
        "✅ **DRS{level}** マッチ成立 — 出発してください！頑張れパイロット 🚀",
        "🚀 **DRS{level}** 全員集合 — 準備ができたら突入！",
    ],
    "notify_match_formed": [
        "✅ **DRS{level}** マッチ成立 — {size}/{size}人揃いました。キューリセット。",
    ],
    "notify_joined_title": "📡 パイロット参加 — DRS{level}",
    "notify_joined": [
        "**{name}** が **DRS{level}** に参加しました！残り {spots} 枠 — 一緒に行きませんか？",
        "🚀 **{name}** が **DRS{level}** に登録！残り {spots} スロット！",
        "⚡ **{name}** が DRS{level} キューに入りました。あと {spots} 人必要！",
        "🎯 **{name}** が **DRS{level}** 準備完了！残り {spots} 枠。",
        "🌟 **{name}** が **DRS{level}** に参加。あと {spots} 人のパイロットを待っています！",
        "📻 新パイロット！**{name}** が **DRS{level}** に登録 — {spots} 枠空きあり。",
        "💫 **{name}** が **DRS{level}** を走りたい！{spots} スロット空き。",
        "🛸 **{name}** が **DRS{level}** に登録。あと {spots} 人で発進！",
        "🔥 **{name}** が **DRS{level}** に参加！残り {spots} 枠。",
        "⭐ **{name}** が **DRS{level}** キューに入りました。{spots} 枠空き！",
    ],
    "notify_qs_title": "▶️ クイックスタート — DRS{level}",
    "notify_qs": [
        "**{name}** が **DRS{level}** を2人で走りたい！▶️ を押して確認してください。",
        "🚀 **{name}** が **DRS{level}** の2人ランを提案！▶️ で発進！",
    ],
    "match_title": "⭐ ダークレッドスター {level} — マッチ #{match_id}",
    "match_footer": "頑張ってください — 星が味方しますように 🌟",
    "match_warning": [
        "⚡ **{names}** — 出発前にテックを設定してください！",
    ],
    "match_warning_multi": [
        "⚡ **{names}** — 出発前にテックを設定してください！",
    ],
    "feedback_prompt": "🏁 DRSランはいかがでしたか？",
    "feedback_thanks": [
        "フィードバックありがとうございます！🌌",
        "記録しました！🚀",
        "ご意見ありがとう！⭐",
    ],
    "feedback_not_participant": "❌ フィードバックはマッチ参加者のみ送信できます。",
    "feedback_already_submitted": "✅ このマッチのフィードバックはすでに送信済みです。",
    "feedback_no_others": "🤔 このマッチに報告できる他のプレイヤーがいません。",
    "feedback_select_player": "誰を報告しますか？下のプレイヤーを選択してください:",
    "feedback_error": "❌ フィードバックを記録できませんでした。もう一度お試しください。",
    "report_thanks": [
        "✅ **{name}** への報告を送信しました。オフィサーに通知されました。",
        "📋 **{name}** をフラグしました。確認されます。",
    ],
    "officer_alert_title": "⚠️ ネガティブレポート",
    "setup_success_title": "✅ DRSボット設定完了",
    "setup_footer": "キューメッセージをキューチャンネルに投稿しました。",
    "setup_roles_success": "✅ ピングロールを更新しました！",
    "setup_no_auth": "❌ 管理者権限またはマネージャーロールが必要です。",
    "status_not_setup": "⚠️ まだ設定されていません。`/drs setup` を実行してください。",
    "status_title": "DRSボット — サーバー設定",
    "lang_set": "✅ 言語を **{lang}** に設定しました。",
}
