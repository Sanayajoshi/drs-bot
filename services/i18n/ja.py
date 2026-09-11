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
        "{icon}**{pilot}** が **{queue}** {count} にロックオン！スラスター点火、ワープ座標待機中！",
        "{icon}パイロット **{pilot}** が **{queue}** {count} のハンガーに着任！全兵装スタンバイ！",
        "{icon}生体反応感知：**{pilot}** が **{queue}** {count} にエントリー！共に出撃する僚機求む！",
        "{icon}**{pilot}** 発着デッキに報告！**{queue}** {count} のワープコイル充電開始！",
        "{icon}艦隊名簿更新：**{pilot}** が **{queue}** {count} に合流。突撃準備完了！",
        "{icon}**{pilot}** コックピット搭乗完了！**{queue}** {count}、各員戦闘配置につけ！",
        "{icon}レーダー反応：**{pilot}** が **{queue}** {count} で待機中。飛び立つ準備はいいか？",
    ],
    "notify_left": [
        "🚪 {icon}**{pilot}** が **{queue}** を離脱しました。ステーションドックへ帰還中。",
        "🚪 {icon}**{pilot}** が **{queue}** の待機命令を解除。スラスター停止。",
        "🚪 {icon}**{pilot}** が **{queue}** のワープ準備を中止。航路クリア。",
        "🚪 {icon}パイロット **{pilot}** は **{queue}** からハンガーへ帰投しました。",
        "🚪 {icon}**{pilot}** が **{queue}** の列から離れました。次のパイロットどうぞ！",
        "🚪 {icon}飛行計画取り下げ：**{pilot}** が **{queue}** を退出しました。次回また！",
    ],
    "notify_left_all": [
        "🚪 {icon}**{pilot}** が全フライトスケジュール（{queues}）を解除し非番に入りました。",
        "🚪 {icon}**{pilot}** が全キュー（{queues}）から退避。ステーションレーダークリア。",
        "🚪 {icon}**{pilot}** 全艦パワーダウン完了。すべてのキューから離脱しました（{queues}）。",
        "🚪 {icon}**{pilot}** の出撃登録が全解除されました（{queues}）。良い休暇を！",
        "🚪 {icon}**{pilot}** がランディングギアを収容し、全キュー（{queues}）から撤収しました。",
    ],
    "notify_qs": [
        "⚡ {icon}{users}**{pilot}** が **{queue}** {count} の **クイックスタート** を起動！2人揃えば即発進！",
        "⚡ {icon}{users}オーバードライブ起動！**{pilot}** が **{queue}** {count} の即時出撃を要請中！",
        "⚡ {icon}{users}**{pilot}** が **{queue}** {count} のクイックスタートを押しました！エンジンを暖めろ！",
        "⚡ {icon}{users}ワープバイパス承認！**{pilot}** は **{queue}** {count} で2機以上の即時跳躍を提案！",
        "⚡ {icon}{users}緊急発進プロトコル発動！**{pilot}** が **{queue}** {count} を急速展開モードに切り替えました！",
    ],
    "notify_extend": [
        "⏳ {icon}**{pilot}** が燃料補給完了：**{queue}** の待機枠を +30分 延長！",
        "⏳ {icon}**{pilot}** が宇宙コーヒーをおかわり：**{queue}** にあと +30分 停泊します！",
        "⏳ {icon}生命維持装置リフレッシュ！**{pilot}** が **{queue}** のチケットを30分延長しました。",
        "⏳ {icon}ワープチャージ維持：**{pilot}** が **{queue}** の待機時間を延長（+30分）！",
        "⏳ {icon}**{pilot}** はまだ帰還しません：**{queue}** のハンガー使用時間を +30分 確保！",
    ],
    "notify_assist": [
        "🆘 {icon}パイロット **{pilot}** が救難フレア発射！支援してくれる僚機求む！",
        "🆘 {icon}**{pilot}** が艦隊護衛＆アシストを要請！ベテランパイロット、手を貸してくれ！",
        "🆘 {icon}艦隊通信：**{pilot}** が **Need Assist** を点灯！護衛可能な指揮官は合流を！",
        "🆘 {icon}戦術支援要請！**{pilot}** が危険宙域へのバックアップを求めています！",
    ],
    "notify_expiry_warning": [
        "⚠️ {icon}<@{user_id}> (**{pilot}**)、**{queue}** のワープ待機枠が **あと5分** で失効します！下の ⏳ を押して延長してください！",
        "⚠️ {icon}警報点滅中：<@{user_id}> (**{pilot}**) の **{queue}** スロットが **あと5分** で流れます！流される前に ⏳ をタップ！",
        "⚠️ {icon}管制塔より <@{user_id}> (**{pilot}**) へ：**{queue}** の発着枠があと5分です！出撃準備または ⏳ で延長を！",
        "⚠️ {icon}生命維持カウントダウン：**{queue}** の残り時間はあと5分です（<@{user_id}>）。延長は ⏳ より！",
    ],
    "notify_expired": [
        "⏰ {icon}<@{user_id}> (**{pilot}**) がセンサー圏外へ離脱 — 無活動のため **{queue}** から除外されました。",
        "⏰ {icon}<@{user_id}> (**{pilot}**) の **{queue}** ハンガー枠が時間切れになりました。枠が開放されます。",
        "⏰ {icon}自動ドック退出：タイムアウトにより <@{user_id}> (**{pilot}**) は **{queue}** から解除されました。",
        "⏰ {icon}<@{user_id}> (**{pilot}**) のレーダー捕捉途絶。**{queue}** の出撃準備は解除されました。準備ができたら再参加を！",
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
