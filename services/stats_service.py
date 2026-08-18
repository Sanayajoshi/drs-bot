from datetime import datetime, timezone, timedelta
from collections import Counter
import discord
import config


def format_seconds_mmss(seconds: float) -> str:
    """Format seconds into M:SS or H:MM:SS."""
    if not seconds or seconds < 0:
        return "0:00"
    total_sec = int(seconds)
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    secs = total_sec % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_hours(seconds: float) -> str:
    """Format total seconds into hours decimal (e.g. 15.20)."""
    if not seconds or seconds < 0:
        return "0.00"
    return f"{seconds / 3600:.2f}"


class StatsService:
    def __init__(self, db):
        self.db = db

    def get_player_stats(self, discord_id: int) -> dict:
        """Fetch and aggregate stats for a specific player."""
        # 1. User Info
        user_row = self.db._execute(
            "SELECT display_name, genesis_level, enrich_level, modt_level, need_assist, created_at FROM users WHERE discord_id = ?",
            (discord_id,), fetch_one=True
        ) or {}

        display_name = user_row.get("display_name") or f"User-{discord_id}"
        gen_lvl = user_row.get("genesis_level", 0) or 0
        enr_lvl = user_row.get("enrich_level", 0) or 0
        rse_lvl = user_row.get("modt_level", 0) or 0

        # 2. Match History
        matches = self.db._execute(
            """SELECT m.id, m.drs_level, m.match_type, m.created_at 
               FROM matches m 
               JOIN match_participants mp ON m.id = mp.match_id 
               WHERE mp.discord_id = ? 
               ORDER BY m.created_at DESC""",
            (discord_id,), fetch_all=True
        ) or []

        total_matches = len(matches)
        
        # Favorite RS Level & Top 3 RS Levels
        level_counter = Counter()
        drs_count = 0
        rs_count = 0
        match_dates = []

        for m in matches:
            m_type = m.get("match_type") or "DRS"
            m_level = m.get("drs_level") or 0
            tag = f"{m_type}{m_level:02d}" if m_level < 10 else f"{m_type}{m_level}"
            level_counter[tag] += 1

            if m_type == "DRS":
                drs_count += 1
            else:
                rs_count += 1

            # Parse date for activity/streak/last active
            if m.get("created_at"):
                try:
                    dt = datetime.strptime(str(m["created_at"]), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                    match_dates.append(dt)
                except Exception:
                    pass

        # Favorite level
        fav_rs = level_counter.most_common(1)[0][0] if level_counter else "N/A"

        # Top 3 RS levels breakdown e.g. DRS10[10] | RS10[7] | DRS09[3]
        top_levels = [f"{tag}[{cnt}]" for tag, cnt in level_counter.most_common(3)]
        top_levels_str = " | ".join(top_levels) if top_levels else "No runs yet"

        # Ratio
        if rs_count > 0:
            drs_rs_ratio = f"{drs_count} DRS / {rs_count} RS ({drs_count/(drs_count+rs_count)*100:.0f}% / {rs_count/(drs_count+rs_count)*100:.0f}%)"
        elif drs_count > 0:
            drs_rs_ratio = f"{drs_count} DRS / 0 RS (100% / 0%)"
        else:
            drs_rs_ratio = "0 DRS / 0 RS"

        # 3. Queue Wait Logs Statistics
        queue_logs = self.db._execute(
            """SELECT queue_type, drs_level, joined_at, left_at, wait_duration_seconds, exit_reason, match_id 
               FROM queue_wait_logs 
               WHERE discord_id = ?""",
            (discord_id,), fetch_all=True
        ) or []

        matched_count = 0
        matched_wait_sec = 0.0

        unmatched_count = 0
        unmatched_wait_sec = 0.0

        for ql in queue_logs:
            dur = float(ql.get("wait_duration_seconds", 0) or 0)
            exit_reason = ql.get("exit_reason", "")
            match_id = ql.get("match_id")

            if exit_reason == "match_created" or match_id is not None:
                matched_count += 1
                matched_wait_sec += dur
            else:
                # Unmatched queue: min wait duration 600s (10 min) to filter out quick join/leaves
                if dur >= 600:
                    unmatched_count += 1
                    unmatched_wait_sec += dur

        # Fallback to matches count if wait logs haven't recorded matched_count
        if matched_count < total_matches:
            matched_count = total_matches

        tot_count = matched_count + unmatched_count
        tot_wait_sec = matched_wait_sec + unmatched_wait_sec

        matched_avg_sec = (matched_wait_sec / matched_count) if matched_count > 0 else 0
        unmatched_avg_sec = (unmatched_wait_sec / unmatched_count) if unmatched_count > 0 else 0
        tot_avg_sec = (tot_wait_sec / tot_count) if tot_count > 0 else 0

        # 4. Teammates (Top 3)
        teammate_rows = self.db._execute(
            """SELECT mp2.discord_id, COUNT(*) as cnt 
               FROM match_participants mp1 
               JOIN match_participants mp2 ON mp1.match_id = mp2.match_id 
               WHERE mp1.discord_id = ? AND mp2.discord_id != ? 
               GROUP BY mp2.discord_id 
               ORDER BY cnt DESC 
               LIMIT 3""",
            (discord_id, discord_id), fetch_all=True
        ) or []

        top_teammates = []
        for t_row in teammate_rows:
            t_id = t_row["discord_id"]
            t_cnt = t_row["cnt"]
            t_user = self.db._execute("SELECT display_name FROM users WHERE discord_id = ?", (t_id,), fetch_one=True)
            t_name = t_user["display_name"] if t_user and t_user.get("display_name") else f"<@{t_id}>"
            top_teammates.append((t_name, t_cnt))

        # 5. Peak Hours & Active Streak & Last Active
        last_active_ts = None
        if match_dates:
            last_active_ts = int(match_dates[0].timestamp())

        # Peak Activity Hours (UTC)
        hour_counter = Counter(dt.hour for dt in match_dates)
        if hour_counter:
            peak_hour = hour_counter.most_common(1)[0][0]
            peak_hours_str = f"{peak_hour:02d}:00 - {(peak_hour+2)%24:02d}:00 UTC"
        else:
            peak_hours_str = "N/A"

        # Active Streak (consecutive days)
        active_streak = 0
        if match_dates:
            sorted_dates = sorted(list({dt.date() for dt in match_dates}), reverse=True)
            today = datetime.utcnow().date()
            if sorted_dates and (today - sorted_dates[0]).days <= 1:
                active_streak = 1
                curr = sorted_dates[0]
                for d in sorted_dates[1:]:
                    if (curr - d).days == 1:
                        active_streak += 1
                        curr = d
                    else:
                        break

        # 6. Max Tech count & SOS
        max_tech_count = 0
        if gen_lvl >= 15:
            max_tech_count += 1
        if enr_lvl >= 15:
            max_tech_count += 1
        if rse_lvl >= 15:
            max_tech_count += 1

        # SOS / Assist requests
        sos_requests = user_row.get("need_assist", 0) or 0

        # Feedback stats
        fb_rows = self.db._execute(
            "SELECT was_positive FROM feedback WHERE discord_id = ?",
            (discord_id,), fetch_all=True
        ) or []
        pos_fb = sum(1 for f in fb_rows if f.get("was_positive") == 1)
        tot_fb = len(fb_rows)

        return {
            "discord_id": discord_id,
            "display_name": display_name,
            "gen_lvl": gen_lvl,
            "enr_lvl": enr_lvl,
            "rse_lvl": rse_lvl,
            "total_matches": total_matches,
            "fav_rs": fav_rs,
            "top_levels_str": top_levels_str,
            "drs_rs_ratio": drs_rs_ratio,
            "matched_count": matched_count,
            "matched_avg_str": format_seconds_mmss(matched_avg_sec),
            "matched_hours_str": format_hours(matched_wait_sec),
            "unmatched_count": unmatched_count,
            "unmatched_avg_str": format_seconds_mmss(unmatched_avg_sec),
            "unmatched_hours_str": format_hours(unmatched_wait_sec),
            "tot_count": tot_count,
            "tot_avg_str": format_seconds_mmss(tot_avg_sec),
            "tot_hours_str": format_hours(tot_wait_sec),
            "top_teammates": top_teammates,
            "last_active_ts": last_active_ts,
            "peak_hours_str": peak_hours_str,
            "active_streak": active_streak,
            "max_tech_count": max_tech_count,
            "sos_requests": sos_requests,
            "pos_fb": pos_fb,
            "tot_fb": tot_fb
        }

    def build_player_stats_embed(self, stats: dict) -> discord.Embed:
        """Construct the Option A styled embed with ASCII tables and clean section headers."""
        embed = discord.Embed(
            title=f"🔴 Red Star Player Stats ┃ {stats['display_name']}",
            color=discord.Color.red()
        )

        # 1. Performance Overview
        fav_suffix = f" ({stats['fav_rs']})" if stats['total_matches'] > 0 else ""
        overview_val = (
            f"**Total Runs:** `{stats['total_matches']}`{fav_suffix}\n"
            f"**Top Levels:** `{stats['top_levels_str']}`\n"
            f"**DRS / RS Ratio:** `{stats['drs_rs_ratio']}`"
        )
        embed.add_field(name="📊 Performance Overview", value=overview_val, inline=False)

        # 2. Queue Wait & Match Table (Option A ASCII Table)
        m_cnt = f"{stats['matched_count']:<5}"
        u_cnt = f"{stats['unmatched_count']:<5}"
        t_cnt = f"{stats['tot_count']:<5}"

        m_avg = f"{stats['matched_avg_str']:<5}"
        u_avg = f"{stats['unmatched_avg_str']:<5}"
        t_avg = f"{stats['tot_avg_str']:<5}"

        m_hrs = f"{stats['matched_hours_str']:<5}"
        u_hrs = f"{stats['unmatched_hours_str']:<5}"
        t_hrs = f"{stats['tot_hours_str']:<5}"

        table_str = (
            "```\n"
            "┌───────────┬──────┬──────┬──────┐\n"
            "│ Match     │ Yes  │ No   │ Tot  │\n"
            "├───────────┼──────┼──────┼──────┤\n"
            f"│ Count     │ {m_cnt}│ {u_cnt}│ {t_cnt}│\n"
            f"│ Avg Wait  │ {m_avg}│ {u_avg}│ {t_avg}│\n"
            f"│ Total Time│ {m_hrs}│ {u_hrs}│ {t_hrs}│\n"
            "└───────────┴──────┴──────┴──────┘\n"
            "```"
        )
        embed.add_field(
            name="⏱️ Queue Wait & Match Stats",
            value=f"{table_str}\n> -# *No-Match count filters out queue exits under 10 minutes.*",
            inline=False
        )

        # 3. Tech & Team Player
        gen_icon = config.EMOJI_GENESIS
        enr_icon = config.EMOJI_ENRICH
        rse_icon = config.EMOJI_MODT
        tech_val = (
            f"**Modules:** {gen_icon} `{stats['gen_lvl']}`  {enr_icon} `{stats['enr_lvl']}`  {rse_icon} `{stats['rse_lvl']}`\n"
            f"**Max Tech Roles:** `{stats['max_tech_count']}` max module(s)\n"
            f"**SOS Requests:** `{stats['sos_requests']}` assist request(s)"
        )
        embed.add_field(name="🛠️ Tech & Team Player", value=tech_val, inline=False)

        # 4. Activity & Engagement
        last_active_str = f"<t:{stats['last_active_ts']}:R>" if stats['last_active_ts'] else "No recent activity"
        activity_val = (
            f"**Active Streak:** `{stats['active_streak']} day(s)` 🔥\n"
            f"**Peak Activity:** `{stats['peak_hours_str']}`\n"
            f"**Last Active:** {last_active_str}"
        )
        embed.add_field(name="⚡ Activity & Engagement", value=activity_val, inline=False)

        # 5. Community & Team Synergy
        if stats["top_teammates"]:
            tm_list = [f"`{name}` ({cnt} runs)" for name, cnt in stats["top_teammates"]]
            synergy_str = " • ".join(tm_list)
        else:
            synergy_str = "No frequent teammates yet"

        fb_str = f"`{stats['pos_fb']}/{stats['tot_fb']}` positive feedback" if stats['tot_fb'] > 0 else "No feedback recorded"

        embed.add_field(
            name="🤝 Community Synergy",
            value=f"**Top Teammates:** {synergy_str}\n**Feedback:** {fb_str}",
            inline=False
        )

        embed.set_footer(text="M.A.L.P. DRS Bot ┃ Player Analytics")
        return embed

