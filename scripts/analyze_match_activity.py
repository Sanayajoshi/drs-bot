#!/usr/bin/env python3
"""
Match Activity & Peak Probability Analyzer for DRS / RS Bot.

This script analyzes match history and queue logs to determine:
1. When a DRS/RS level is most active (Hourly breakdown 00:00 - 23:00).
2. Day-of-week probability distribution (Mon-Sun).
3. 7x24 Heatmap of highest match probability.
4. Average queue wait times during different time windows.
5. Queue success probability (matches formed vs expired/cancelled).

Usage:
  python3 scripts/analyze_match_activity.py --level 9
  python3 scripts/analyze_match_activity.py --level 9 --tz-offset -5   # e.g. EST/EDT
  python3 scripts/analyze_match_activity.py --level 9 --simulate      # Seed test data if empty
  python3 scripts/analyze_match_activity.py --level 9 --html activity_drs9.html
"""

import os
import sys
import math
import random
import sqlite3
import argparse
from datetime import datetime, timedelta, timezone

DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
DAYS_SHORT = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def get_db_connection(db_path: str) -> sqlite3.Connection:
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def simulate_sample_data(conn: sqlite3.Connection, level: int = 9, match_type: str = "DRS", num_matches: int = 400):
    """Generates realistic synthetic matches across a 30-day period for testing."""
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drs_level INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'completed',
            created_at TEXT NOT NULL,
            queue_duration_seconds INTEGER DEFAULT 0,
            feedback_sent_at TEXT,
            match_type TEXT NOT NULL DEFAULT 'DRS'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS queue_wait_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id INTEGER NOT NULL,
            queue_type TEXT NOT NULL,
            drs_level INTEGER NOT NULL,
            joined_at TEXT NOT NULL,
            left_at TEXT NOT NULL,
            wait_duration_seconds INTEGER NOT NULL,
            exit_reason TEXT NOT NULL,
            match_id INTEGER
        )
    """)

    now = datetime.now(timezone.utc)
    print(f"[*] Generating {num_matches} sample matches for {match_type} {level} over the past 30 days...")

    matches_to_insert = []
    logs_to_insert = []

    # Activity pattern: Peak on Fri/Sat/Sun evenings (17:00 - 23:00 UTC)
    # Secondary peak around 12:00 - 14:00 UTC
    for i in range(num_matches):
        days_ago = random.uniform(0, 30)
        base_time = now - timedelta(days=days_ago)

        # Realistic hour selection with peaks
        if random.random() < 0.65:
            # Evening peak
            hour = random.choice([16, 17, 18, 19, 20, 21, 22, 23])
        elif random.random() < 0.25:
            # Mid-day peak
            hour = random.choice([11, 12, 13, 14, 15])
        else:
            # Low activity hours
            hour = random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        match_time = base_time.replace(hour=hour, minute=minute, second=second)
        time_str = match_time.strftime("%Y-%m-%d %H:%M:%S")

        # Faster wait times during peak hours
        if hour in [18, 19, 20, 21, 22]:
            wait_sec = random.randint(60, 360)
        else:
            wait_sec = random.randint(300, 1800)

        matches_to_insert.append((level, "completed", time_str, wait_sec, match_type))

    cur.executemany(
        "INSERT INTO matches (drs_level, status, created_at, queue_duration_seconds, match_type) VALUES (?, ?, ?, ?, ?)",
        matches_to_insert
    )

    # Also generate queue wait logs (including some timeouts/expired queues)
    for row in matches_to_insert:
        m_level, _, time_str, wait_sec, m_type = row
        # 3 participants for DRS, 4 for RS
        p_count = 3 if m_type == "DRS" else 4
        for p in range(p_count):
            uid = 1000000 + random.randint(1, 80)
            logs_to_insert.append((uid, m_type, m_level, time_str, time_str, wait_sec, "match_formed", None))

    # Add some expired queues during off-peak hours
    for _ in range(int(num_matches * 0.15)):
        days_ago = random.uniform(0, 30)
        off_time = now - timedelta(days=days_ago)
        off_time = off_time.replace(hour=random.choice([3, 4, 5, 6, 7]), minute=random.randint(0, 59))
        time_str = off_time.strftime("%Y-%m-%d %H:%M:%S")
        uid = 1000000 + random.randint(1, 80)
        logs_to_insert.append((uid, match_type, level, time_str, time_str, 1800, "expired", None))

    cur.executemany(
        "INSERT INTO queue_wait_logs (discord_id, queue_type, drs_level, joined_at, left_at, wait_duration_seconds, exit_reason, match_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        logs_to_insert
    )
    conn.commit()
    print("[+] Sample data generation completed successfully.\n")


def query_match_stats(conn: sqlite3.Connection, level: int, match_type: str = "DRS", tz_offset: int = 0):
    """
    Analyzes match data with optional timezone shifting.
    SQLite date modifier: '+N hours' or '-N hours'
    """
    cur = conn.cursor()

    # Check if table exists and has rows
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='matches'")
    if not cur.fetchone():
        return None

    # Timezone modifier for SQLite strftime
    tz_mod = f"{tz_offset:+d} hours" if tz_offset != 0 else "+0 hours"

    # 1. Total matches for this tier
    if match_type.upper() == "ALL":
        cur.execute("SELECT COUNT(*) FROM matches WHERE drs_level = ?", (level,))
    else:
        cur.execute(
            "SELECT COUNT(*) FROM matches WHERE drs_level = ? AND (match_type = ? OR match_type IS NULL)",
            (level, match_type)
        )
    total_matches = cur.fetchone()[0]

    if total_matches == 0:
        return {
            "total_matches": 0,
            "hourly": [],
            "daily": [],
            "heatmap": [[0]*24 for _ in range(7)],
            "wait_times": {},
            "success_rate": None,
            "tz_offset": tz_offset
        }

    # Date range
    type_cond = "" if match_type.upper() == "ALL" else f"AND (match_type = '{match_type}' OR match_type IS NULL)"
    cur.execute(f"SELECT MIN(created_at), MAX(created_at) FROM matches WHERE drs_level = ? {type_cond}", (level,))
    min_date, max_date = cur.fetchone()

    # 2. Hourly breakdown (0-23)
    # strftime('%H', datetime(created_at, tz_mod))
    hourly_query = f"""
        SELECT 
            CAST(strftime('%H', datetime(created_at, '{tz_mod}')) AS INTEGER) AS hr,
            COUNT(*) AS match_count,
            ROUND(AVG(queue_duration_seconds), 1) AS avg_wait_sec
        FROM matches
        WHERE drs_level = ? {type_cond}
        GROUP BY hr
        ORDER BY hr ASC
    """
    cur.execute(hourly_query, (level,))
    hourly_dict = {row["hr"]: (row["match_count"], row["avg_wait_sec"]) for row in cur.fetchall()}

    hourly = []
    for h in range(24):
        cnt, avg_w = hourly_dict.get(h, (0, 0))
        pct = (cnt / total_matches * 100.0) if total_matches > 0 else 0.0
        hourly.append({
            "hour": h,
            "count": cnt,
            "percentage": pct,
            "avg_wait_sec": avg_w or 0
        })

    # 3. Day of week breakdown (0=Sun, 1=Mon, ..., 6=Sat)
    daily_query = f"""
        SELECT 
            CAST(strftime('%w', datetime(created_at, '{tz_mod}')) AS INTEGER) AS day_idx,
            COUNT(*) AS match_count,
            ROUND(AVG(queue_duration_seconds), 1) AS avg_wait_sec
        FROM matches
        WHERE drs_level = ? {type_cond}
        GROUP BY day_idx
        ORDER BY day_idx ASC
    """
    cur.execute(daily_query, (level,))
    daily_dict = {row["day_idx"]: (row["match_count"], row["avg_wait_sec"]) for row in cur.fetchall()}

    daily = []
    for d in range(7):
        cnt, avg_w = daily_dict.get(d, (0, 0))
        pct = (cnt / total_matches * 100.0) if total_matches > 0 else 0.0
        daily.append({
            "day_idx": d,
            "day_name": DAYS_OF_WEEK[d],
            "day_short": DAYS_SHORT[d],
            "count": cnt,
            "percentage": pct,
            "avg_wait_sec": avg_w or 0
        })

    # 4. 7 x 24 Heatmap Matrix: (day_idx, hour)
    heatmap_query = f"""
        SELECT 
            CAST(strftime('%w', datetime(created_at, '{tz_mod}')) AS INTEGER) AS day_idx,
            CAST(strftime('%H', datetime(created_at, '{tz_mod}')) AS INTEGER) AS hr,
            COUNT(*) AS match_count
        FROM matches
        WHERE drs_level = ? {type_cond}
        GROUP BY day_idx, hr
    """
    cur.execute(heatmap_query, (level,))
    heatmap = [[0]*24 for _ in range(7)]
    for row in cur.fetchall():
        d_idx = row["day_idx"]
        h_idx = row["hr"]
        heatmap[d_idx][h_idx] = row["match_count"]

    # 5. Success rate calculation (queue_wait_logs + match_participants fallback)
    success_rate = None
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='match_participants'")
    has_mp = cur.fetchone() is not None

    total_player_runs = 0
    if has_mp:
        cur.execute(f"""
            SELECT COUNT(*) FROM match_participants mp
            JOIN matches m ON mp.match_id = m.id
            WHERE m.drs_level = ? {type_cond}
        """, (level,))
        mp_row = cur.fetchone()
        if mp_row:
            total_player_runs = mp_row[0] or 0

    if total_player_runs == 0 and total_matches > 0:
        # Fallback estimation based on squad size (3 for DRS, 4 for RS)
        squad_size = 3 if match_type.upper() == "DRS" else 4
        total_player_runs = total_matches * squad_size

    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='queue_wait_logs'")
    has_qwl = cur.fetchone() is not None

    if has_qwl:
        type_q = "" if match_type.upper() == "ALL" else f"AND (queue_type = '{match_type}' OR queue_type IS NULL)"
        cur.execute(f"""
            SELECT 
                COUNT(*) as total_logged,
                SUM(CASE WHEN exit_reason IN ('matched', 'match_formed') OR match_id IS NOT NULL THEN 1 ELSE 0 END) as formed_count,
                SUM(CASE WHEN exit_reason IN ('expired', 'timeout') THEN 1 ELSE 0 END) as expired_count,
                SUM(CASE WHEN exit_reason IN ('user_exit', 'manual_exit', 'cancelled') THEN 1 ELSE 0 END) as cancelled_count
            FROM queue_wait_logs
            WHERE drs_level = ? {type_q}
        """, (level,))
        log_row = cur.fetchone()

        formed = (log_row["formed_count"] or 0) if log_row else 0
        expired = (log_row["expired_count"] or 0) if log_row else 0
        cancelled = (log_row["cancelled_count"] or 0) if log_row else 0

        # If formed_count is 0 in logs (e.g. older matches prior to queue_wait_logs logging "matched"),
        # use the known player runs from the matches table
        if formed == 0 and total_player_runs > 0:
            formed = total_player_runs

        effective_total = formed + expired + cancelled
        if effective_total > 0:
            prob_pct = round((formed / effective_total) * 100.0, 1)
        elif total_matches > 0:
            prob_pct = 100.0
            effective_total = total_player_runs
            formed = total_player_runs
        else:
            prob_pct = 0.0

        success_rate = {
            "total_queues": effective_total,
            "formed": formed,
            "expired": expired,
            "cancelled": cancelled,
            "match_probability_pct": prob_pct,
            "player_runs": total_player_runs
        }
    elif total_matches > 0:
        success_rate = {
            "total_queues": total_player_runs,
            "formed": total_player_runs,
            "expired": 0,
            "cancelled": 0,
            "match_probability_pct": 100.0,
            "player_runs": total_player_runs
        }

    return {
        "total_matches": total_matches,
        "min_date": min_date,
        "max_date": max_date,
        "hourly": hourly,
        "daily": daily,
        "heatmap": heatmap,
        "success_rate": success_rate,
        "tz_offset": tz_offset
    }


def render_ascii_charts(stats: dict, level: int, match_type: str):
    """Outputs high-clarity terminal visualizations."""
    total = stats["total_matches"]
    tz = stats["tz_offset"]
    tz_str = f"UTC{tz:+d}:00" if tz != 0 else "UTC"

    print("=" * 76)
    print(f"📊 MATCH ACTIVITY & PROBABILITY REPORT — {match_type.upper()} {level}")
    print(f"⏰ Timezone Reference: {tz_str} | Total Matches Analyzed: {total}")
    if stats.get("min_date") and stats.get("max_date"):
        print(f"📅 Historical Period:  {stats['min_date']}  to  {stats['max_date']}")
    print("=" * 76)

    if total == 0:
        print("\n⚠️ No matches found in the database for this tier yet.")
        print("💡 Tip: You can test this report right now with synthetic data by running:")
        print(f"   python3 scripts/analyze_match_activity.py --level {level} --simulate\n")
        return

    # Success probability summary if available
    if stats.get("success_rate"):
        sr = stats["success_rate"]
        print(f"\n🎯 Overall Queue Match Probability: {sr['match_probability_pct']}%")
        print(f"   (Formed: {sr['formed']} | Expired: {sr['expired']} | Cancelled: {sr['cancelled']} | Total Queues: {sr['total_queues']})")

    # -------------------------------------------------------------
    # 1. Hourly Distribution Bar Chart
    # -------------------------------------------------------------
    print(f"\n🕒 HOURLY ACTIVITY DISTRIBUTION (00:00 - 23:00 {tz_str})")
    print("-" * 76)
    print("Hour   Matches   Share    Avg Wait    Probability Visual (Each █ ≈ 2%)")
    print("-" * 76)

    max_hourly_cnt = max((h["count"] for h in stats["hourly"]), default=1) or 1
    for h in stats["hourly"]:
        hr_str = f"{h['hour']:02d}:00"
        cnt = h["count"]
        pct = h["percentage"]
        wait_m = round(h["avg_wait_sec"] / 60.0, 1) if h["avg_wait_sec"] else 0
        wait_str = f"{wait_m}m" if wait_m > 0 else "-"
        # Bar scale: up to 30 chars
        bar_len = int(round((cnt / max_hourly_cnt) * 30))
        bar = "█" * bar_len
        print(f"{hr_str}   {cnt:>5}    {pct:>5.1f}%   {wait_str:>7}    |{bar:<30}|")

    # -------------------------------------------------------------
    # 2. Day of Week Breakdown
    # -------------------------------------------------------------
    print(f"\n📅 DAY OF WEEK ACTIVITY BREAKDOWN")
    print("-" * 76)
    print("Day         Matches   Share    Avg Wait    Activity Indicator")
    print("-" * 76)
    max_daily_cnt = max((d["count"] for d in stats["daily"]), default=1) or 1
    for d in stats["daily"]:
        cnt = d["count"]
        pct = d["percentage"]
        wait_m = round(d["avg_wait_sec"] / 60.0, 1) if d["avg_wait_sec"] else 0
        wait_str = f"{wait_m}m" if wait_m > 0 else "-"
        bar_len = int(round((cnt / max_daily_cnt) * 25))
        bar = "█" * bar_len
        print(f"{d['day_name']:<10}  {cnt:>5}    {pct:>5.1f}%   {wait_str:>7}    |{bar:<25}|")

    # -------------------------------------------------------------
    # 3. 7 x 24 Heatmap Matrix
    # -------------------------------------------------------------
    print(f"\n🗺️ 7x24 HOURLY PROBABILITY HEATMAP ({tz_str})")
    print("   [Key: . = Inactive, ░ = Low, ▒ = Moderate, ▓ = Active, █ = Peak Hotspot]")
    print("-" * 76)
    header = "Day  " + "".join(f"{h:02d} " for h in range(24))
    print(header)

    grid = stats["heatmap"]
    max_cell = max(max(row) for row in grid) if grid else 1
    if max_cell == 0:
        max_cell = 1

    for d_idx in range(7):
        row_str = f"{DAYS_SHORT[d_idx]}  "
        for h_idx in range(24):
            val = grid[d_idx][h_idx]
            ratio = val / max_cell
            if val == 0:
                char = " . "
            elif ratio < 0.25:
                char = " ░ "
            elif ratio < 0.55:
                char = " ▒ "
            elif ratio < 0.85:
                char = " ▓ "
            else:
                char = " █ "
            row_str += char
        print(row_str)

    # -------------------------------------------------------------
    # 4. Top Peak Windows Recommendation
    # -------------------------------------------------------------
    peak_slots = []
    for d_idx in range(7):
        for h_idx in range(24):
            val = grid[d_idx][h_idx]
            if val > 0:
                peak_slots.append((val, d_idx, h_idx))
    peak_slots.sort(key=lambda x: x[0], reverse=True)

    print("\n🏆 TOP RECOMMENDED QUEUE TIMES (Highest Probability of Instant Match):")
    if peak_slots:
        for rank, (matches, d_idx, h_idx) in enumerate(peak_slots[:5], 1):
            day_name = DAYS_OF_WEEK[d_idx]
            time_window = f"{h_idx:02d}:00 - {(h_idx+1)%24:02d}:00 {tz_str}"
            pct_of_all = (matches / total) * 100.0
            print(f"  #{rank} {day_name:<9} at {time_window:<16} → {matches} matches ({pct_of_all:.1f}% share)")
    else:
        print("  Not enough data to calculate peaks.")
    print("=" * 76 + "\n")


def generate_html_dashboard(stats: dict, level: int, match_type: str, output_path: str):
    """Generates an elegant standalone HTML dashboard with embedded SVG charts."""
    total = stats["total_matches"]
    tz = stats["tz_offset"]
    tz_str = f"UTC{tz:+d}:00" if tz != 0 else "UTC"

    grid = stats["heatmap"]
    max_cell = max(max(row) for row in grid) if grid and total > 0 else 1
    if max_cell == 0:
        max_cell = 1

    # Generate Heatmap table HTML
    heatmap_rows = []
    for d_idx in range(7):
        cells = []
        for h_idx in range(24):
            val = grid[d_idx][h_idx]
            intensity = val / max_cell
            # Gradient from soft dark neutral to vibrant emerald / cyan
            if val == 0:
                bg = "rgba(255, 255, 255, 0.03)"
                text_c = "#4b5563"
            elif intensity < 0.25:
                bg = f"rgba(14, 165, 233, {0.2 + intensity * 0.4})"
                text_c = "#bae6fd"
            elif intensity < 0.6:
                bg = f"rgba(59, 130, 246, {0.3 + intensity * 0.5})"
                text_c = "#ffffff"
            elif intensity < 0.85:
                bg = f"rgba(99, 102, 241, {0.5 + intensity * 0.5})"
                text_c = "#ffffff"
            else:
                bg = f"rgba(16, 185, 129, {0.7 + intensity * 0.3})"
                text_c = "#ffffff"

            cells.append(
                f'<td title="{DAYS_OF_WEEK[d_idx]} {h_idx:02d}:00 — {val} matches" '
                f'style="background:{bg}; color:{text_c}; text-align:center; padding:8px 4px; font-size:12px; font-family:monospace; border-radius:4px;">'
                f'{val if val > 0 else "·"}</td>'
            )
        heatmap_rows.append(f'<tr><td style="font-weight:600; padding:6px 12px; color:#9ca3af;">{DAYS_SHORT[d_idx]}</td>{"".join(cells)}</tr>')

    hours_header = "".join(f'<th style="padding:4px; font-size:11px; color:#6b7280; font-family:monospace;">{h:02d}</th>' for h in range(24))

    # Generate Hourly Bar chart SVG
    max_hourly = max((h["count"] for h in stats["hourly"]), default=1) or 1
    svg_bars = []
    svg_w = 720
    svg_h = 160
    bar_w = 22
    gap = 7
    start_x = 20

    for i, h in enumerate(stats["hourly"]):
        x = start_x + i * (bar_w + gap)
        h_ratio = h["count"] / max_hourly
        bar_height = max(int(h_ratio * 120), 4 if h["count"] > 0 else 0)
        y = svg_h - 25 - bar_height

        # color
        color = "#10b981" if h_ratio > 0.75 else ("#3b82f6" if h_ratio > 0.3 else "#4b5563")
        svg_bars.append(
            f'<rect x="{x}" y="{y}" width="{bar_w}" height="{bar_height}" rx="3" fill="{color}" opacity="0.9">'
            f'<title>{h["hour"]:02d}:00 - {h["count"]} matches ({h["percentage"]:.1f}%)</title>'
            f'</rect>'
        )
        svg_bars.append(
            f'<text x="{x + bar_w/2}" y="{svg_h - 8}" font-size="9" fill="#9ca3af" text-anchor="middle" font-family="monospace">{h["hour"]:02d}</text>'
        )
        if h["count"] > 0:
            svg_bars.append(
                f'<text x="{x + bar_w/2}" y="{y - 4}" font-size="9" fill="#d1d5db" text-anchor="middle" font-family="monospace">{h["count"]}</text>'
            )

    svg_content = f"""
    <svg viewBox="0 0 {svg_w} {svg_h}" style="width:100%; height:auto; display:block;">
        {"".join(svg_bars)}
    </svg>
    """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{match_type.upper()} {level} — Match Activity & Peak Probability Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #0f172a;
            color: #f8fafc;
            margin: 0;
            padding: 24px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        .header {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }}
        h1 {{ margin: 0 0 6px 0; font-size: 24px; color: #38bdf8; }}
        h2 {{ margin: 0 0 16px 0; font-size: 17px; color: #cbd5e1; border-bottom: 1px solid #334155; padding-bottom: 8px; }}
        .badge {{
            display: inline-block;
            background: #0284c7;
            color: white;
            padding: 4px 10px;
            border-radius: 9999px;
            font-size: 12px;
            font-weight: 600;
        }}
        table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 2px;
        }}
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 20px;
        }}
        .stat-box {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 16px;
        }}
        .stat-num {{ font-size: 26px; font-weight: 700; color: #38bdf8; }}
        .stat-label {{ font-size: 13px; color: #94a3b8; margin-top: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>🎯 {match_type.upper()} {level} Activity Probability</h1>
                <div style="color:#94a3af; font-size:14px;">Timezone: {tz_str} | Sample Window: {stats.get('min_date', 'N/A')} to {stats.get('max_date', 'N/A')}</div>
            </div>
            <div>
                <span class="badge">{total} Total Matches</span>
            </div>
        </div>

        <div class="stat-grid">
            <div class="stat-box">
                <div class="stat-num">{total}</div>
                <div class="stat-label">Total Completed Matches</div>
            </div>
            <div class="stat-box">
                <div class="stat-num">{stats.get('success_rate', {}).get('player_runs', total * (3 if match_type.upper() == 'DRS' else 4))}</div>
                <div class="stat-label">Total Player Runs</div>
            </div>
            <div class="stat-box">
                <div class="stat-num">{stats.get('success_rate', {}).get('match_probability_pct', '100')}%</div>
                <div class="stat-label">Queue Match Probability</div>
                <div style="font-size:11px; color:#64748b; margin-top:4px;">
                    Formed: {stats.get('success_rate', {}).get('formed', total * 3)} · Expired: {stats.get('success_rate', {}).get('expired', 0)} · Left: {stats.get('success_rate', {}).get('cancelled', 0)}
                </div>
            </div>
            <div class="stat-box">
                <div class="stat-num">{tz_str}</div>
                <div class="stat-label">Reference Timezone</div>
            </div>
        </div>

        <div class="card">
            <h2>📈 Hourly Activity Distribution (00:00 - 23:00)</h2>
            {svg_content}
        </div>

        <div class="card">
            <h2>🗺️ 7x24 Probability Heatmap (Day × Hour)</h2>
            <div style="overflow-x:auto;">
                <table>
                    <thead>
                        <tr>
                            <th style="text-align:left; padding:4px 12px; color:#6b7280; font-size:11px;">DAY</th>
                            {hours_header}
                        </tr>
                    </thead>
                    <tbody>
                        {"".join(heatmap_rows)}
                    </tbody>
                </table>
            </div>
            <div style="margin-top:14px; font-size:12px; color:#94a3b8; display:flex; gap:16px; align-items:center;">
                <span>Density:</span>
                <span style="display:inline-block; width:12px; height:12px; background:rgba(255,255,255,0.05); border-radius:2px;"></span> Inactive
                <span style="display:inline-block; width:12px; height:12px; background:rgba(14,165,233,0.5); border-radius:2px;"></span> Low
                <span style="display:inline-block; width:12px; height:12px; background:rgba(59,130,246,0.7); border-radius:2px;"></span> Moderate
                <span style="display:inline-block; width:12px; height:12px; background:rgba(16,185,129,0.9); border-radius:2px;"></span> Peak Hotspot
            </div>
        </div>
    </div>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✨ Interactive HTML report saved to: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Analyze when DRS / RS matches are most active.")
    parser.add_argument("--db", default="drs_bot.db", help="Path to SQLite database file (default: drs_bot.db)")
    parser.add_argument("--level", type=int, default=9, help="DRS or RS tier level to analyze (default: 9)")
    parser.add_argument("--type", default="DRS", help="Match type: 'DRS', 'RS', or 'ALL' (default: DRS)")
    parser.add_argument("--tz-offset", type=int, default=0, help="Timezone offset in hours from UTC (e.g. -5 for EST, +0 for UTC)")
    parser.add_argument("--simulate", action="store_true", help="Generate 400 realistic sample matches to test analysis immediately")
    parser.add_argument("--html", default=None, help="Save a visual standalone HTML report (e.g. drs9_activity.html)")

    args = parser.parse_args()

    conn = get_db_connection(args.db)

    if args.simulate:
        simulate_sample_data(conn, level=args.level, match_type=args.type)

    stats = query_match_stats(conn, level=args.level, match_type=args.type, tz_offset=args.tz_offset)
    if not stats:
        print(f"❌ Error: Could not read database table 'matches' from {args.db}.")
        sys.exit(1)

    render_ascii_charts(stats, level=args.level, match_type=args.type)

    if args.html:
        generate_html_dashboard(stats, level=args.level, match_type=args.type, output_path=args.html)


if __name__ == "__main__":
    main()

