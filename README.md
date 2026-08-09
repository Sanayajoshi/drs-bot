# DRS Queue Bot (Dark Red Star Bot)

A multi-server Discord bot built with Python (`discord.py`) for managing **Hades' Star Dark Red Star (DRS)** queues, automated matchmaking, cross-server thread communication with real-time translation, corporation bonus tracking, feedback/reporting, and community engagement statistics.

---

## 📐 System Architecture Overview

```
                          ┌──────────────────────────┐
                          │         app.py           │
                          │   (DRSBot Entry Point)   │
                          └────────────┬─────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            │                                                     │
┌───────────▼───────────┐                             ┌───────────▼───────────┐
│     config.py         │                             │    db/database.py     │
│ (Settings & Constants)│                             │ (SQLite Operations)   │
└───────────────────────┘                             └───────────┬───────────┘
                                                                  │
┌─────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────┐
│                                                           Cogs / Extensions                                                       │
├───────────────┬───────────────┬───────────────┬────────────────┬─────────────────┬────────────────┬───────────────┬───────────────┤
│   setup_cog   │   queue_cog   │   match_cog   │   thread_cog   │  feedback_cog   │   officer_cog  │   bonus_cog   │engagement_cog │
└───────┬───────┴───────┬───────┴───────┬───────┴───────┬────────┴────────┬────────┴───────┬────────┴───────┬───────┴───────┬───────┘
        │               │               │               │                 │                │                │               │
┌───────▼───────┬───────▼───────┬───────▼───────┬───────▼────────┬────────▼────────┬───────▼────────┬───────▼───────┬───────▼───────┐
│   Services    │  QueueService │  MatchService │ ThreadService  │ Feedback/Modal  │  Database Ops  │ BonusService  │ FactsService  │
│  & Utilities  │  & UIService  │               │ & MyMemory i18n│ & Officer Alert │  & Mod Relay   │  & Web Scraper│  & Engagement │
└───────────────┴───────────────┴───────────────┴────────────────┴─────────────────┴────────────────┴───────────────┴───────────────┘
```

---

## 📂 Repository Structure

| Path | Purpose |
| :--- | :--- |
| `app.py` | Main entry point; initializes bot, SQLite DB, Cogs, background tasks, and syncs slash commands. |
| `config.py` | Bot settings, queue sizes, intervals, supported languages, and Super Admin user IDs. |
| `requirements.txt` | Dependency specifications (`discord.py`, `aiohttp`, `beautifulsoup4`, `python-dotenv`). |
| `db/database.py` | SQLite database manager (`DatabaseOperations`) handling schema, migrations, queries, and transactions. |
| `cogs/setup_cog.py` | `/drs` slash commands for server configuration, roles, languages, and status. |
| `cogs/queue_cog.py` | Queue UI renderer, button handlers, 5-min expiry loop, QuickStart, and sync loop. |
| `cogs/match_cog.py` | Listener for `on_drs_match_formed` event to trigger thread creation. |
| `cogs/thread_cog.py` | Cross-server match thread creation, tech level display, bell ping, relay & auto-translation. |
| `cogs/feedback_cog.py` | Post-match feedback prompt, `ReportModal` for issue reporting, officer channel alert dispatch. |
| `cogs/officer_cog.py` | `/officer` management commands, stats, server listing, match lookups, and live officer chat relay. |
| `cogs/bonus_cog.py` | Slash commands for managing auto-fetched corporation bonuses (`/add_corporation`, etc.). |
| `cogs/engagement_cog.py` | Community facts, leaderboard stats, `/postfact`, `/setfactfrequency`, and automated fact loops. |
| `services/bonus_service.py` | Web scraper (`https://ws.tsl.rocks/corp/`) using BeautifulSoup & `aiohttp` for corp bonuses. |
| `services/facts_service.py` | Generator for 7 engagement embed types (Leaderboards, Top Corps, Activity Radar, Morale, etc.). |
| `services/match_service.py` | Helper wrapper around database operations for match participants. |
| `services/queue_service.py` | Business logic for joining/leaving queue, QuickStart execution, and 3-player match formation. |
| `services/thread_service.py` | Build match intro embeds, bell ping view, and MyMemory API translation wrapper. |
| `services/ui_service.py` | Discord Embed & Button View builders for the interactive queue panel. |
| `services/i18n/` | Internationalization dictionary files (`en`, `ja`, `es`, `de`, `hi`, `pl`, `fr`). |

---

## 🗄️ Database Schema (`drs_bot.db`)

All tables use SQLite with `PRAGMA journal_mode=WAL` and `PRAGMA foreign_keys=ON`.

### 1. `servers`
Stores per-guild configuration settings.
* `guild_id` (INTEGER PRIMARY KEY)
* `queue_channel_id` (INTEGER)
* `queue_message_id` (INTEGER)
* `notification_channel_id` (INTEGER)
* `officer_channel_id` (INTEGER)
* `manager_role_id` (INTEGER)
* `language` (TEXT NOT NULL DEFAULT 'en')
* `role_drs7` .. `role_drs12` (INTEGER)
* `fact_frequency_hours` (INTEGER DEFAULT 4)
* `last_fact_sent` (TEXT)
* `created_at` (TEXT)

### 2. `users`
Global user profiles and module/tech levels.
* `discord_id` (INTEGER PRIMARY KEY)
* `display_name` (TEXT NOT NULL)
* `genesis_level` (INTEGER, 6–15)
* `enrich_level` (INTEGER, 6–15)
* `modt_level` (INTEGER, 6–15)
* `need_assist` (INTEGER DEFAULT 0)
* `created_at` (TEXT)

### 3. `user_servers`
Tracks which servers a user belongs to and when they were last seen.
* `discord_id` (INTEGER REFERENCES users)
* `guild_id` (INTEGER REFERENCES servers)
* `display_name` (TEXT NOT NULL)
* `last_seen` (TEXT)
* Primary Key: (`discord_id`, `guild_id`)

### 4. `queue_entries`
Active players currently in queue.
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
* `discord_id` (INTEGER REFERENCES users)
* `drs_level` (INTEGER, 7–12)
* `expires_at` (TEXT NOT NULL)
* `joined_at` (TEXT)
* `quick_start` (INTEGER DEFAULT 0)
* `queue_guild_id` (INTEGER)

### 5. `matches`
Formed match records.
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
* `drs_level` (INTEGER NOT NULL)
* `status` (TEXT DEFAULT 'active')
* `created_at` (TEXT)

### 6. `match_participants`
Participants in a match (preserves origin `queue_guild_id` even after queue deletion).
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
* `match_id` (INTEGER REFERENCES matches)
* `discord_id` (INTEGER REFERENCES users)
* `queue_guild_id` (INTEGER)

### 7. `match_threads`
Maps formed matches to Discord threads across guilds.
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
* `match_id` (INTEGER REFERENCES matches)
* `guild_id` (INTEGER REFERENCES servers)
* `thread_id` (INTEGER NOT NULL)
* `created_at` (TEXT)

### 8. `feedback`
Post-match positive/negative feedback submissions.
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
* `match_id` (INTEGER REFERENCES matches)
* `discord_id` (INTEGER REFERENCES users)
* `was_positive` (INTEGER NOT NULL)
* `submitted_at` (TEXT)

### 9. `feedback_reports`
Detailed player issue reports.
* `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
* `match_id` (INTEGER REFERENCES matches)
* `reporter_id` (INTEGER REFERENCES users)
* `reported_player_id` (INTEGER REFERENCES users)
* `issue_type` (TEXT NOT NULL) — `no_show`, `behavior`, `performance`, `other`
* `comment` (TEXT)
* `thread_id` (INTEGER)
* `created_at` (TEXT)

### 10. `corp_bonuses` & `tracked_corps`
Manual guild bonuses (`corp_bonuses`) and auto-fetched 64-hex corp bonuses from tsl.rocks (`tracked_corps`).
* `tracked_corps`: `corp_id` (64-hex string), `corp_name`, `bonus_pct`, `last_fetched`, `is_active`, `fetch_error`, `created_at`.

---

## 🛠️ Complete Slash Command Reference

### Server Setup Commands (`/drs`)
| Command | Description | Permission |
| :--- | :--- | :--- |
| `/drs setup` | Set queue channel, notification channel, officer channel, and manager role. | Admin / Officer / Dev |
| `/drs roles` | Assign role pings for levels DRS7 through DRS12. | Admin / Officer / Dev |
| `/drs language` | Change server display language (`en`, `ja`, `es`, `de`, `hi`, `pl`, `fr`). | Admin / Officer / Dev |
| `/drs status` | Display current server bot configuration. | Admin / Officer / Dev |

### Officer & Admin Management (`/officer`)
| Command | Description | Permission |
| :--- | :--- | :--- |
| `/officer stats` | View network-wide match statistics & ratings. | Officer / Dev |
| `/officer servers` | List installed servers, member counts, and configured language. | Officer / Dev |
| `/officer match <id>` | Inspect match details, players, tech levels, feedback, and threads. | Officer / Dev |
| `/officer level <drs_level>` | View recent matches for a specific DRS level. | Officer / Dev |
| `/officer players` | Leaderboard of top pilots by match count. | Officer / Dev |
| `/officer queue` | Real-time snapshot of active queues across all levels. | Officer / Dev |
| `/officer bonus_set` | Open UI modal to set manual corporation bonus % and duration. | Officer / Dev |
| `/officer bonus_list` | List active and expired manual corporation bonuses. | Officer / Dev |
| `/list_servers` / `/officer list_servers` | [Admin Only] Detailed list of servers, member counts, join timestamps, and invites. | Super Admin Only |

### Corporation Bonus Tracking (`BonusCog`)
| Command | Description | Permission |
| :--- | :--- | :--- |
| `/add_corporation <corp_id> [name]` | Track 64-hex corp ID for hourly web-scraped bonus updates. | Super Admin Only |
| `/remove_corporation <corp_id>` | Remove corporation from auto-tracking. | Super Admin Only |
| `/list_corporations` | List active tracked corporations and their scraped bonuses. | Everyone |
| `/force_update_bonuses` | Force immediate scrape update of all tracked corp bonuses. | Super Admin Only |

### Engagement & Facts (`EngagementCog`)
| Command | Description | Permission |
| :--- | :--- | :--- |
| `/postfact` (or `!postfact`) | Post a random engagement fact/stats embed immediately. | Super Admin Only |
| `/setfactfrequency <hours>` | Set automatic engagement fact posting frequency (1–168 hours). | Admin / Officer / Super Admin |

---

## 🎮 Interactive Queue Panel Controls

The main queue panel is rendered dynamically by `UIService` and updated automatically by `QueueCog`.

```
[ 7️⃣ ] [ 8️⃣ ] [ 9️⃣ ] [ ▶️ QuickStart ]
[ 🔟 ] [ 11 ] [ 12 ] [ ⏳ Extend     ]
[ GEN] [ ENR] [ RSE] [ ❌ Leave      ]
[      🆘 Need Assist                ]
```

* **DRS 7–12 Buttons**: Toggle join/leave for specific DRS level queues (default timer: 30 minutes).
* **▶️ QuickStart**: Request early match start when 2 players are queued. Matches immediately if both select QuickStart.
* **⏳ Extend**: Extends current queue expiration time by +30 minutes. Re-fires role ping notification.
* **GEN / ENR / RSE Buttons**: Open dropdown to set tech levels (Genesis, Enrich, Research/ModT level 6–15).
* **❌ Leave**: Leaves all active queues immediately.
* **🆘 Need Assist**: Toggles SOS assistance badge on your queue listing.

---

## ⚙️ Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Sanayajoshi/drs-bot.git
   cd drs-bot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env` file in the project root:
   ```env
   TOKEN=your_discord_bot_token_here
   DB_PATH=drs_bot.db
   ```

4. **Run the Bot**:
   ```bash
   python app.py
   ```

