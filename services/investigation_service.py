import logging
from datetime import datetime, timezone, timedelta
from collections import Counter
import discord
import config

logger = logging.getLogger("investigation_service")

ISSUE_MAP = {
    "no_show": "No Show 👻",
    "behavior": "Behavior 🚨",
    "performance": "Performance 📉",
    "other": "Other ❓",
}

ISSUE_ICONS = {
    "no_show": "👻",
    "behavior": "🚨",
    "performance": "📉",
    "other": "❓",
}


def parse_datetime(val) -> datetime | None:
    if not val:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val
    try:
        dt = datetime.strptime(str(val), "%Y-%m-%d %H:%M:%S")
        return dt.replace(tzinfo=timezone.utc)
    except Exception:
        try:
            dt = datetime.fromisoformat(str(val))
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None


def get_timeframe_range(timeframe: str) -> tuple[datetime | None, datetime | None, str]:
    """
    Returns (start_dt, end_dt, label) in UTC.
    Supported presets: '7d', '30d', 'last_month', 'all'.
    """
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    if timeframe == "7d":
        start = now - timedelta(days=7)
        return start, now, "Last 7 Days"
    elif timeframe == "last_month":
        # First day of current month
        first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Last day of prev month
        last_of_prev_month = first_of_this_month - timedelta(seconds=1)
        # First day of prev month
        first_of_prev_month = last_of_prev_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_name = first_of_prev_month.strftime("%B %Y")
        return first_of_prev_month, first_of_this_month, f"Last Month ({month_name})"
    elif timeframe == "all":
        return None, None, "All Time"
    else:  # default 30d
        start = now - timedelta(days=30)
        return start, now, "Last 30 Days"


class InvestigationService:
    def __init__(self, db):
        self.db = db

    # ------------------------------------------------------------------
    # 1. Quick helper for investigation threads: Past reports for a player
    # ------------------------------------------------------------------

    def get_player_past_incidents_summary(self, player_id: int, exclude_report_id: int | None = None) -> str:
        """
        Returns a concise 1-2 line summary of past incidents for a reported player,
        used directly inside newly created officer investigation threads.
        """
        query = "SELECT id, issue_type, resolved_at FROM feedback_reports WHERE reported_player_id = ?"
        params = [player_id]
        if exclude_report_id:
            query += " AND id != ?"
            params.append(exclude_report_id)

        rows = self.db._execute(query, tuple(params), fetch_all=True) or []
        if not rows:
            return "✅ **No prior reports** recorded for this player."

        total = len(rows)
        open_cnt = sum(1 for r in rows if not r.get("resolved_at"))
        resolved_cnt = total - open_cnt

        issue_counts = Counter(r.get("issue_type", "other") for r in rows)
        issue_parts = []
        for itype, cnt in issue_counts.most_common():
            label = ISSUE_MAP.get(itype, itype.title())
            issue_parts.append(f"{cnt} {label}")
        issue_breakdown = ", ".join(issue_parts)

        return (
            f"⚠️ **{total} prior report(s):** {issue_breakdown}\n"
            f"↳ *Status:* `{open_cnt} 🔴 Open` · `{resolved_cnt} 🟢 Resolved`"
        )

    # ------------------------------------------------------------------
    # 2. Player Investigation Dossier
    # ------------------------------------------------------------------

    def get_player_dossier(self, player_id: int) -> dict:
        """Fetch detailed investigation data for a single player."""
        # Player record
        user = self.db._execute(
            "SELECT discord_id, display_name, created_at FROM users WHERE discord_id = ?",
            (player_id,), fetch_one=True
        ) or {}
        display_name = user.get("display_name") or f"Pilot-{player_id}"
        registered_at = user.get("created_at") or "Unknown"

        # Match history & level breakdown
        matches = self.db._execute(
            """SELECT m.id, m.drs_level, m.match_type, m.created_at
               FROM matches m
               JOIN match_participants mp ON m.id = mp.match_id
               WHERE mp.discord_id = ?
               ORDER BY m.created_at DESC""",
            (player_id,), fetch_all=True
        ) or []
        total_runs = len(matches)

        level_counter = Counter()
        for m in matches:
            m_type = m.get("match_type") or "DRS"
            m_lvl = m.get("drs_level") or 0
            tag = f"{m_type}{m_lvl}"
            level_counter[tag] += 1

        levels_breakdown_str = " · ".join(
            f"`{tag}` ({cnt})" for tag, cnt in level_counter.most_common()
        ) or "No completed runs"

        # Feedback stats for matches this player took part in
        fb_rows = self.db._execute(
            "SELECT was_positive FROM feedback WHERE discord_id = ?",
            (player_id,), fetch_all=True
        ) or []
        pos_fb = sum(1 for f in fb_rows if f.get("was_positive") == 1)
        neg_fb = sum(1 for f in fb_rows if f.get("was_positive") == 0)
        tot_fb = len(fb_rows)

        # Reports filed AGAINST this player
        reports_against_raw = self.db._execute(
            """SELECT fr.*, ur.display_name AS reporter_name,
                      ures.display_name AS resolver_name, m.drs_level, m.match_type
               FROM feedback_reports fr
               JOIN users ur ON ur.discord_id = fr.reporter_id
               LEFT JOIN users ures ON ures.discord_id = fr.resolved_by
               LEFT JOIN matches m ON m.id = fr.match_id
               WHERE fr.reported_player_id = ?
               ORDER BY fr.created_at DESC""",
            (player_id,), fetch_all=True
        ) or []

        total_reports_against = len(reports_against_raw)
        open_against = sum(1 for r in reports_against_raw if not r.get("resolved_at"))
        resolved_against = total_reports_against - open_against

        infractions_counter = Counter(r.get("issue_type", "other") for r in reports_against_raw)
        infractions_parts = []
        for itype, cnt in infractions_counter.most_common():
            label = ISSUE_MAP.get(itype, itype.title())
            infractions_parts.append(f"`{cnt}` {label}")
        infractions_str = " · ".join(infractions_parts) if infractions_parts else "None"

        # Reports filed BY this player
        reports_filed_by_cnt = self.db._execute(
            "SELECT COUNT(*) AS cnt FROM feedback_reports WHERE reporter_id = ?",
            (player_id,), fetch_one=True
        )
        filed_by_total = reports_filed_by_cnt["cnt"] if reports_filed_by_cnt else 0

        # Attach investigation thread ids for recent reports
        reports_against = []
        for r in reports_against_raw[:6]:
            r_dict = dict(r)
            r_threads = self.db.get_report_threads(r["id"])
            r_dict["threads"] = r_threads
            reports_against.append(r_dict)

        return {
            "player_id": player_id,
            "display_name": display_name,
            "registered_at": registered_at,
            "total_runs": total_runs,
            "levels_breakdown_str": levels_breakdown_str,
            "pos_fb": pos_fb,
            "neg_fb": neg_fb,
            "tot_fb": tot_fb,
            "total_reports_against": total_reports_against,
            "open_against": open_against,
            "resolved_against": resolved_against,
            "infractions_str": infractions_str,
            "filed_by_total": filed_by_total,
            "reports_against": reports_against,
        }

    def build_player_dossier_embed(self, dossier: dict) -> discord.Embed:
        """Construct the rich Player Incident Dossier Embed."""
        p_id = dossier["player_id"]
        embed = discord.Embed(
            title=f"🛡️ Player Incident Dossier ┃ {dossier['display_name']}",
            color=discord.Color.red() if dossier["open_against"] > 0 else (
                discord.Color.gold() if dossier["total_reports_against"] > 0 else discord.Color.green()
            ),
            description=f"**User ID:** `{p_id}` (<@{p_id}>) · **Registered:** `{dossier['registered_at'][:10]}`"
        )

        # 1. Run History & Conduct Overview
        tot_runs = dossier["total_runs"]
        tot_fb = dossier["tot_fb"]
        pos_fb = dossier["pos_fb"]
        neg_fb = dossier["neg_fb"]

        if tot_fb > 0:
            fb_pct = (pos_fb / tot_fb) * 100
            fb_summary = (
                f"`{pos_fb}` 👍 Positive · `{neg_fb}` ⚠️ Reported "
                f"({fb_pct:.1f}% positive of `{tot_fb}` rating(s) submitted across `{tot_runs}` runs)"
            )
        else:
            fb_summary = f"No run ratings submitted yet (across `{tot_runs}` total runs)"

        levels_str = dossier['levels_breakdown_str']
        if len(levels_str) > 300:
            levels_str = levels_str[:295] + "…"

        overview_lines = [
            f"• **Total Completed Runs:** `{tot_runs}`",
            f"• **Runs by Level:** {levels_str}",
            f"• **Feedback Ratings:** {fb_summary}",
            f"• **Reports Against Player:** **`{dossier['total_reports_against']}`** total "
            f"({dossier['open_against']} 🔴 Open · {dossier['resolved_against']} 🟢 Resolved)",
            f"• **Reports Filed By Player:** `{dossier['filed_by_total']}` report(s)",
            f"• **Infractions Breakdown:** {dossier['infractions_str']}",
        ]
        overview_val = "\n".join(overview_lines)
        if len(overview_val) > 1024:
            overview_val = overview_val[:1020] + "…"

        embed.add_field(
            name="📊 Run History & Conduct Overview",
            value=overview_val,
            inline=False
        )

        # 2. Detailed Incident History (Tickets against them as individual fields)
        recent_reports = dossier["reports_against"]
        if not recent_reports:
            embed.add_field(
                name="⚠️ Incident History",
                value="✅ **Clean Record** — No incident tickets have ever been filed against this player.",
                inline=False
            )
        else:
            for r in recent_reports[:6]:
                issue_label = ISSUE_MAP.get(r.get("issue_type", "other"), r.get("issue_type", "Other"))
                created_dt = parse_datetime(r.get("created_at"))
                ts_str = f"<t:{int(created_dt.timestamp())}:R>" if created_dt else r.get("created_at", "")

                m_id = r.get("match_id")
                drs_lvl = r.get("drs_level")
                match_label = f"Match #{m_id}" + (f" (DRS{drs_lvl})" if drs_lvl else "")

                status_icon = "🟢" if r.get("resolved_at") else "🔴"
                status_word = "Resolved" if r.get("resolved_at") else "Open"
                field_name = f"🎫 Ticket #{r['id']} ┃ {issue_label} · {status_icon} {status_word}"

                lines = [
                    f"• **Match:** {match_label} · Filed {ts_str}",
                    f"• **Filed By:** {r.get('reporter_name', 'Unknown')} (<@{r.get('reporter_id')}>)",
                ]

                if r.get("comment"):
                    lines.append(f"• **Comment:** *\"{r['comment'][:150]}\"*")

                if r.get("resolved_at"):
                    res_dt = parse_datetime(r["resolved_at"])
                    res_ts = f"<t:{int(res_dt.timestamp())}:R>" if res_dt else r["resolved_at"]
                    res_by = f"**{r.get('resolver_name', 'Officer')}** (<@{r.get('resolved_by')}>)"
                    lines.append(f"• **Resolved By:** {res_by} · {res_ts}")
                    if r.get("resolution_notes"):
                        lines.append(f"• **Resolution:** {r['resolution_notes'][:150]}")
                else:
                    lines.append(f"• **Status:** 🔴 **Open Investigation**")

                if r.get("threads"):
                    thread_mentions = " ".join(f"<#{t['thread_id']}>" for t in r["threads"])
                    lines.append(f"• **Officer Threads:** {thread_mentions}")
                elif r.get("thread_id"):
                    lines.append(f"• **Original Match Thread:** <#{r['thread_id']}>")

                val = "\n".join(lines)
                if len(val) > 1024:
                    val = val[:1020] + "…"
                embed.add_field(name=field_name[:256], value=val, inline=False)

        embed.set_footer(text="DRS Bot Investigation System ┃ Confidential Officer Record")
        return embed

    # ------------------------------------------------------------------
    # 3. Incident Logs / Ledger
    # ------------------------------------------------------------------

    def get_incident_logs(
        self,
        timeframe: str = "30d",
        issue_type: str | None = None,
        status: str | None = None,
        limit: int = 15
    ) -> tuple[list[dict], str]:
        """Query incident reports filtered by timeframe, issue_type, and status."""
        start_dt, end_dt, tf_label = get_timeframe_range(timeframe)

        conditions = []
        params = []

        if start_dt:
            conditions.append("fr.created_at >= ?")
            params.append(start_dt.strftime("%Y-%m-%d %H:%M:%S"))
        if end_dt:
            conditions.append("fr.created_at <= ?")
            params.append(end_dt.strftime("%Y-%m-%d %H:%M:%S"))

        if issue_type and issue_type != "all":
            conditions.append("fr.issue_type = ?")
            params.append(issue_type)

        if status == "open":
            conditions.append("fr.resolved_at IS NULL")
        elif status == "resolved":
            conditions.append("fr.resolved_at IS NOT NULL")

        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        query = f"""
            SELECT fr.*,
                   ur.display_name AS reporter_name,
                   up.display_name AS reported_name,
                   ures.display_name AS resolver_name,
                   m.drs_level, m.match_type
            FROM feedback_reports fr
            JOIN users ur ON ur.discord_id = fr.reporter_id
            JOIN users up ON up.discord_id = fr.reported_player_id
            LEFT JOIN users ures ON ures.discord_id = fr.resolved_by
            LEFT JOIN matches m ON m.id = fr.match_id
            {where_clause}
            ORDER BY fr.created_at DESC
            LIMIT ?
        """
        params.append(limit)

        rows = self.db._execute(query, tuple(params), fetch_all=True) or []
        results = []
        for r in rows:
            r_dict = dict(r)
            r_dict["threads"] = self.db.get_report_threads(r["id"])
            results.append(r_dict)

        return results, tf_label

    def build_incident_logs_embed(
        self,
        tickets: list[dict],
        tf_label: str,
        issue_type: str | None = None,
        status: str | None = None
    ) -> discord.Embed:
        """Construct the filtered incident logs embed."""
        status_label = "All Statuses"
        if status == "open":
            status_label = "🔴 Open Only"
        elif status == "resolved":
            status_label = "🟢 Resolved Only"

        issue_label = ISSUE_MAP.get(issue_type, "All Types") if issue_type and issue_type != "all" else "All Types"

        embed = discord.Embed(
            title="📋 Incident Reports Log",
            color=discord.Color.blurple(),
            description=(
                f"**Timeframe:** `{tf_label}` · **Status:** `{status_label}` · **Issue:** `{issue_label}`\n"
                f"Found **{len(tickets)}** ticket(s)"
            )
        )

        if not tickets:
            embed.add_field(
                name="No Records",
                value="No incident reports matched your filter criteria.",
                inline=False
            )
            return embed

        max_ticket_fields = 24  # Embeds support up to 25 fields
        shown_tickets = tickets[:max_ticket_fields]

        for r in shown_tickets:
            created_dt = parse_datetime(r.get("created_at"))
            ts_str = f"<t:{int(created_dt.timestamp())}:R>" if created_dt else r.get("created_at", "")
            type_label = ISSUE_MAP.get(r.get("issue_type", "other"), r.get("issue_type", "Other"))

            status_icon = "🟢" if r.get("resolved_at") else "🔴"
            status_tag = "Resolved" if r.get("resolved_at") else "Open"
            field_name = f"🎫 Ticket #{r['id']} ┃ {type_label} · {status_icon} {status_tag}"

            match_info = f"Match #{r.get('match_id')}"
            if r.get("drs_level"):
                match_info += f" (DRS{r.get('drs_level')})"

            lines = [
                f"• **Target:** **{r.get('reported_name')}** (<@{r.get('reported_player_id')}>)",
                f"• **Reporter:** {r.get('reporter_name')} (<@{r.get('reporter_id')}>) · {ts_str}",
                f"• **Context:** {match_info}",
            ]

            if r.get("comment"):
                comment_snippet = r["comment"][:120] + ("…" if len(r["comment"]) > 120 else "")
                lines.append(f"• **Comment:** *\"{comment_snippet}\"*")

            if r.get("resolved_at"):
                res_by = r.get("resolver_name") or f"<@{r.get('resolved_by')}>"
                lines.append(f"• **Resolved By:** {res_by}")
                if r.get("resolution_notes"):
                    notes_snippet = r["resolution_notes"][:90] + ("…" if len(r["resolution_notes"]) > 90 else "")
                    lines.append(f"• **Resolution:** {notes_snippet}")
            elif r.get("threads"):
                thread_refs = " ".join(f"<#{t['thread_id']}>" for t in r["threads"])
                lines.append(f"• **Investigation Threads:** {thread_refs}")

            field_val = "\n".join(lines)
            if len(field_val) > 1024:
                field_val = field_val[:1020] + "…"

            embed.add_field(name=field_name[:256], value=field_val, inline=False)

        if len(tickets) > max_ticket_fields:
            remaining = len(tickets) - max_ticket_fields
            embed.add_field(
                name="ℹ️ Additional Tickets",
                value=f"Showing top {max_ticket_fields} of **{len(tickets)}** tickets. Narrow filters or use `/investigate player`.",
                inline=False
            )

        embed.set_footer(text="Use /officer resolve_report <id> [notes] or in-thread buttons to close tickets.")
        return embed

    # ------------------------------------------------------------------
    # 4. Incident Summary & Health Metrics
    # ------------------------------------------------------------------

    def get_incident_summary(self, timeframe: str = "30d") -> tuple[dict, str]:
        """Aggregate statistical metrics regarding incident volume, resolutions, and repeat subjects."""
        start_dt, end_dt, tf_label = get_timeframe_range(timeframe)

        # 1. Total matches in timeframe
        match_query = "SELECT COUNT(*) AS cnt FROM matches"
        match_params = []
        if start_dt:
            match_query += " WHERE created_at >= ?"
            match_params.append(start_dt.strftime("%Y-%m-%d %H:%M:%S"))
        if end_dt:
            match_query += " AND created_at <= ?" if start_dt else " WHERE created_at <= ?"
            match_params.append(end_dt.strftime("%Y-%m-%d %H:%M:%S"))

        match_row = self.db._execute(match_query, tuple(match_params), fetch_one=True)
        total_matches = match_row["cnt"] if match_row else 0

        # 2. Reports in timeframe
        report_query = """
            SELECT fr.id, fr.issue_type, fr.reported_player_id, fr.created_at,
                   fr.resolved_at, up.display_name AS reported_name
            FROM feedback_reports fr
            JOIN users up ON up.discord_id = fr.reported_player_id
        """
        report_conditions = []
        report_params = []
        if start_dt:
            report_conditions.append("fr.created_at >= ?")
            report_params.append(start_dt.strftime("%Y-%m-%d %H:%M:%S"))
        if end_dt:
            report_conditions.append("fr.created_at <= ?")
            report_params.append(end_dt.strftime("%Y-%m-%d %H:%M:%S"))

        if report_conditions:
            report_query += f" WHERE {' AND '.join(report_conditions)}"

        reports = self.db._execute(report_query, tuple(report_params), fetch_all=True) or []
        total_reports = len(reports)

        # Resolution rate
        resolved_cnt = 0
        res_durations_sec = []
        issue_counter = Counter()
        subject_counter = Counter()
        subject_issues = {}

        for r in reports:
            itype = r.get("issue_type", "other")
            issue_counter[itype] += 1

            p_id = r["reported_player_id"]
            p_name = r.get("reported_name") or f"Pilot-{p_id}"
            subject_counter[(p_id, p_name)] += 1
            if (p_id, p_name) not in subject_issues:
                subject_issues[(p_id, p_name)] = Counter()
            subject_issues[(p_id, p_name)][itype] += 1

            if r.get("resolved_at"):
                resolved_cnt += 1
                c_dt = parse_datetime(r.get("created_at"))
                r_dt = parse_datetime(r.get("resolved_at"))
                if c_dt and r_dt and r_dt >= c_dt:
                    res_durations_sec.append((r_dt - c_dt).total_seconds())

        open_cnt = total_reports - resolved_cnt
        res_rate = (resolved_cnt / total_reports * 100) if total_reports > 0 else 100.0
        report_rate = (total_reports / total_matches * 100) if total_matches > 0 else 0.0

        avg_res_hours = (sum(res_durations_sec) / len(res_durations_sec) / 3600) if res_durations_sec else 0.0

        # Repeat subjects (2 or more reports against them in this period)
        repeat_subjects = []
        for (p_id, p_name), cnt in subject_counter.most_common():
            if cnt >= 2:
                issues_str = ", ".join(
                    f"{icnt} {ISSUE_ICONS.get(itype, itype)}"
                    for itype, icnt in subject_issues[(p_id, p_name)].items()
                )
                repeat_subjects.append({
                    "player_id": p_id,
                    "display_name": p_name,
                    "count": cnt,
                    "issues_str": issues_str,
                })

        return {
            "total_matches": total_matches,
            "total_reports": total_reports,
            "report_rate": report_rate,
            "resolved_cnt": resolved_cnt,
            "open_cnt": open_cnt,
            "res_rate": res_rate,
            "avg_res_hours": avg_res_hours,
            "issue_counter": issue_counter,
            "repeat_subjects": repeat_subjects,
        }, tf_label

    def build_incident_summary_embed(self, summary: dict, tf_label: str) -> discord.Embed:
        """Construct the high-level Incident & Conduct Summary Embed."""
        embed = discord.Embed(
            title=f"📈 Incident & Conduct Summary ┃ {tf_label}",
            color=discord.Color.blurple(),
            description="Overview of network match health, incident volume, and dispute resolutions:"
        )

        # 1. Match & Report Totals
        res_time_str = f"{summary['avg_res_hours']:.1f} hours" if summary["avg_res_hours"] > 0 else "N/A"
        totals_lines = [
            f"• **Total Formed Matches:** `{summary['total_matches']}`",
            f"• **Incident Reports Filed:** **`{summary['total_reports']}`** ({summary['report_rate']:.1f}% of runs reported)",
            f"• **Resolution Rate:** **`{summary['res_rate']:.1f}%`** (`{summary['resolved_cnt']}` 🟢 Resolved · `{summary['open_cnt']}` 🔴 Open)",
            f"• **Avg Resolution Time:** `{res_time_str}`",
        ]
        embed.add_field(name="📌 Match & Report Totals", value="\n".join(totals_lines), inline=False)

        # 2. Issue Breakdown with bar visualization
        tot_rep = summary["total_reports"]
        if tot_rep == 0:
            embed.add_field(name="🏷️ Issue Breakdown", value="✅ No incidents filed during this timeframe.", inline=False)
        else:
            bar_lines = []
            for itype in ["no_show", "behavior", "performance", "other"]:
                cnt = summary["issue_counter"].get(itype, 0)
                pct = (cnt / tot_rep * 100) if tot_rep > 0 else 0
                label = ISSUE_MAP.get(itype, itype.title())
                # 10-char ASCII bar
                bar_len = int(round(pct / 10))
                bar_str = "█" * bar_len + "░" * (10 - bar_len)
                bar_lines.append(f"• **{label}:** `{cnt:>2}` ({pct:>4.1f}%) `[{bar_str}]`")

            embed.add_field(name="🏷️ Issue Breakdown", value="\n".join(bar_lines), inline=False)

        # 3. Repeat Subjects
        repeats = summary["repeat_subjects"]
        if repeats:
            repeat_lines = []
            for idx, item in enumerate(repeats, start=1):
                line = f"{idx}. **{item['display_name']}** (<@{item['player_id']}>) — **`{item['count']}` reports** ({item['issues_str']})"
                if sum(len(l) + 1 for l in repeat_lines) + len(line) > 900:
                    remaining = len(repeats) - len(repeat_lines)
                    repeat_lines.append(f"... and {remaining} more repeat subject(s)")
                    break
                repeat_lines.append(line)

            val = "\n".join(repeat_lines)
            if len(val) > 1024:
                val = val[:1020] + "…"

            embed.add_field(
                name=f"⚠️ Repeat Subjects ({len(repeats)} with 2+ reports)",
                value=val,
                inline=False
            )
        else:
            embed.add_field(
                name="⚠️ Repeat Subjects",
                value="✅ No repeat offenders found (no player with 2+ reports in this period).",
                inline=False
            )

        embed.set_footer(text="DRS Bot Investigation System ┃ Network Safety & Conduct Analytics")
        return embed

