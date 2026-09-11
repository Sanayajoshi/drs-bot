"""Japanese strings for the DRS bot."""

GEN_EMOJI = "<:Genesis:1519930122566635652>"
ENR_EMOJI = "<:Enrich:1519930167005413466>"
RSE_EMOJI = "<:ModTRSE:1256962175398842399>"
_11_EMOJI = "<:11:1378449282688090184>"
_12_EMOJI = "<:12:1519933592401215570>"

STRINGS: dict = {
    # Pinned Queue Embed Titles & Texts
    "queue_title_drs": "ダークレッドスター キュー",
    "queue_title_rs": "レッドスター キュー",
    "queue_empty_drs": "*ハンガーにパイロットはいません。下のレベルボタンを押して出撃準備！*",
    "queue_empty_rs": "*レッドスターキュー待機中のパイロットはいません。レベルを選択して艦隊を編成しましょう！*",
    "queue_title": "⭐ ダークレッドスター キュー",
    "queue_empty": "*パイロット募集中。番号を押して参加しよう！*",
    "queue_footer": "毎分更新 · レベルボタンでキュー参加/退出",
    "queue_legend": f"> -# `キュー切替`: 7️⃣–{_12_EMOJI}\n> -# `キュー退出`: ❌\n> -# `テック設定   `: {GEN_EMOJI} {ENR_EMOJI} {RSE_EMOJI}\n> -# `時間追加(30分)`: ⏳\n> -# `デュオ開始   `: ▶️",

    # Channel Notifications (Broadcasts)
    "notify_joined": [
        "{icon}パイロット **{pilot}** が **{queue}** {count} に参加 · 発進準備完了",
        "{icon}パイロット **{pilot}** が **{queue}** {count} に参加 · 発着デッキ待機中",
        "{icon}パイロット **{pilot}** が **{queue}** {count} に参加 · 全システム稼働",
    ],
    "notify_left": [
        "🚪 {icon}パイロット **{pilot}** が **{queue}** を離脱 · 離脱完了",
        "🚪 {icon}パイロット **{pilot}** が **{queue}** を離脱 · ステーションへ帰投",
        "🚪 {icon}パイロット **{pilot}** が **{queue}** を離脱 · スタンバイ解除",
    ],
    "notify_left_all": [
        "🚪 {icon}パイロット **{pilot}** が全キュー（{queues}）を離脱 · ステーションへ帰投",
        "🚪 {icon}パイロット **{pilot}** が全キュー（{queues}）を離脱 · フライト解除",
    ],
    "notify_qs": [
        "⚡ {icon}{users}パイロット **{pilot}** が **{queue}** {count} のクイックスタートを有効化",
        "⚡ {icon}{users}パイロット **{pilot}** が **{queue}** {count} のクイックスタートを要請",
    ],
    "notify_extend": [
        "⏳ {icon}パイロット **{pilot}** が **{queue}** の待機枠を延長（+30分）",
    ],
    "notify_assist": [
        "🆘 {icon}パイロット **{pilot}** が **{queue}** の艦隊護衛を要請",
    ],
    "notify_expiry_warning": [
        "⚠️ {icon}パイロット <@{user_id}>：**{queue}** の待機枠はあと **5分** で失効します（⏳ で延長）",
    ],
    "notify_expired": [
        "⏰ {icon}パイロット <@{user_id}> が **{queue}** を離脱 · 時間切れ",
        "⏰ {icon}パイロット <@{user_id}> はセンサー圏外のため **{queue}** から除外されました",
    ],
    "notify_match_formed_title": [
        "⚔️ {queue} レベル {level} 艦隊集結！(Match #{match_id})",
        "🚀 艦隊編成完了：{queue}{level}！(Match #{match_id})",
        "💥 戦闘群出撃準備完了：{queue}{level}！(Match #{match_id})",
        "🌌 ワープゲート同期：{queue}{level}！(Match #{match_id})",
    ],
    "notify_match_formed_desc": [
        "⏱️ **マッチ成立時間:** {duration}\n\n**出撃パイロット:**\n{roster}\n\n🛰️ *ワープ座標固定！マッチスレッドにて兵装を確認してください！*",
        "⏱️ **艦隊編成所要時間:** {duration}\n\n**分隊名簿:**\n{roster}\n\n🔥 *全兵装ホット、シールド展開。マッチスレッドへ向かってください！*",
        "⏱️ **待機時間:** {duration}\n\n**パイロット集結:**\n{roster}\n\n🚀 *宙域クリア、戦利品を掴み取れ！戦闘スレッドへ集合！*",
    ],

    # Personal Ephemeral Responses (User Button Clicks)
    "ephemeral_joined": [
        "✅ **{queue}** にロックイン！タイマー開始（30分）。僚機の合流を待て！",
        "✅ **{queue}** の出撃許可証を発行！有効期限は30分です。",
        "✅ コックピット密閉！**{queue}** の待機列に入りました（30分）。",
        "✅ ドッキングクランプ解除！次の30分間、**{queue}** で待機します。",
        "✅ 航路コンピューター設定完了：**{queue}**（30分）。健闘を祈る！",
    ],
    "ephemeral_left": [
        "👋 **{queue}** を離脱しました。ハンガードア開放。",
        "👋 **{queue}** から撤退。ゆっくり休んでください、パイロット！",
        "👋 **{queue}** の枠を開放しました。",
        "👋 **{queue}** の飛行計画をキャンセルしました。",
        "👋 **{queue}** のスラスター停止。また次回！",
    ],
    "ephemeral_left_all": [
        "🚪 全アクティブキューから退出しました。全航路クリア。",
        "🚪 全艦パワーダウン。すべてのキューから離脱しました。",
        "🚪 全キューから離脱完了。カンティーナで会いましょう！",
        "🚪 DRSおよびRSの全スロットを返上しました。",
    ],
    "ephemeral_extended": [
        "⏳ キュー枠（**{queues}**）を +30分 延長しました！ワープコイル保持。",
        "⏳ **{queues}** に +30分 追加！ロケット燃料を補給する時間は十分あります。",
        "⏳ 生命維持リフィル完了！**{queues}** に +30分 付与。",
        "⏳ **{queues}** のハンガー枠更新完了（+30分）！",
    ],
    "ephemeral_qs": [
        "⚡ **{queue}** のクイックスタート起動！2人集まれば即発進します。",
        "⚡ **{queue}** のオーバードライブ作動！待機なしモード有効。",
        "⚡ クイックスタート準備完了！僚機の合図で飛び立ちます！",
    ],
    "ephemeral_assist_on": [
        "🆘 Need Assist を **ON** にしました！救難ビーコン点灯 — 他のパイロットに支援要請が表示されます。",
        "🆘 アシスト要請有効！護衛僚機を求めていることがキューに表示されます。",
    ],
    "ephemeral_assist_off": [
        "✅ Need Assist を **OFF** にしました。通常飛行プロトコルへ復帰。",
        "✅ アシストフラグ解除。SOSビーコンを停止しました。",
    ],

    # Legacy & Modal Keys
    "joined": [
        "✅ **{queue}** に参加！残り時間: {time}\n📋 参加中: **{levels}**",
        "🚀 **{queue}** 確定！タイマー: {time}。\n📋 キュー: **{levels}**",
        "⚡ **{queue}** 登録完了！{time} 残り。\n📋 参加中: **{levels}**",
    ],
    "left_level": [
        "👋 **{queue}** を退出。残り: **{levels}**",
        "🚪 **{queue}** 離脱。残りキュー: **{levels}**",
    ],
    "left_level_all_gone": [
        "👋 **{queue}** 退出 — キュークリア。",
        "🚪 **{queue}** を退出。全キュー離脱。",
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
        "🔥 **{queue}** マッチ成立！スレッドを確認してください。",
        "⚡ **{queue}** 開始！スレッドへどうぞ。",
    ],
    "qs_not_queued": [
        "❓ キューに参加していません。まず参加してください。",
    ],
    "qs_multi_queue": [
        "⚠️ 複数キューに参加中です（{levels}）。▶️ には1つのキューのみ必要です。",
    ],
    "qs_alone": [
        "🧍 **{queue}** に他のプレイヤーがいません。最低2人必要です！",
    ],
    "qs_already": [
        "⏳ すでに ▶️ を押しました。相手の確認を待っています。",
    ],
    "qs_confirmed": [
        "🚀 クイックスタート確定！**{queue}** 発進！スレッドを確認してください。",
    ],
    "qs_sent": [
        "▶️ **{queue}** のクイックスタートリクエストを送信しました！確認待ち。",
    ],
    "mod_set": [
        "✅ **{mod}** レベルを **{level}** に設定しました！",
        "💾 **{mod}** → **{level}** 保存完了！",
    ],
    "mod_prompt": "現在の **{mod}** レベル: **{current}**\n新しいレベルを選択してください:",
    "mod_not_set": "未設定",
    "expiry_warning": [
        "⏰ **{name}** — **{queue}** のスロットがあと5分で期限切れです！⏳ で延長してください。",
        "🚨 **{name}** — {queue} のタイマーが切れそうです！今すぐ延長しましょう。",
    ],
    "expiry_extend_prompt": "⏳ 30分追加",
    "expiry_extended_ok": "✅ **{queue}** キューに30分追加しました！",
    "expiry_not_yours": "🤔 このボタンはあなた用ではありません。",
    "match_proceed": [
        "✅ **{queue}** マッチ成立 — 出発してください！頑張れパイロット 🚀",
        "🚀 **{queue}** 全員集合 — 準備ができたら突入！",
    ],
    "match_title": "⭐ {queue} — マッチ #{match_id}",
    "match_footer": "頑張ってください — 星が味方しますように 🌟",
    "match_warning": [
        "⚡ **{names}** — 出発前にテックを設定してください！",
    ],
    "match_warning_multi": [
        "⚡ **{names}** — 出発前にテックを設定してください！",
    ],
    "feedback_prompt": "🏁 ランはいかがでしたか？",
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
    "setup_success_title": "✅ ボット設定完了",
    "setup_footer": "キューメッセージをキューチャンネルに投稿しました。",
    "setup_roles_success": "✅ ピングロールを更新しました！",
    "setup_no_auth": "❌ 管理者権限またはマネージャーロールが必要です。",
    "status_not_setup": "⚠️ まだ設定されていません。`/drs setup` を実行してください。",
    "status_title": "キューボット — サーバー設定",
    "lang_set": "✅ 言語を **{lang}** に設定しました。",
}
