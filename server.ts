import express from "express";
import cors from "cors";
import dotenv from "dotenv";
import * as cheerio from "cheerio";
import { Client, GatewayIntentBits, ActivityType, REST, Routes, SlashCommandBuilder } from "discord.js";

dotenv.config();

const PORT = parseInt(process.env.PORT || "3000", 10);
const BOT_TOKEN = process.env.DISCORD_BOT_TOKEN || "";

// Configuration Constants
const DRS_LEVELS = [7, 8, 9, 10, 11, 12];
const RS_LEVELS = [4, 5, 6, 7, 8, 9, 10, 11, 12];
const MATCH_SIZE_DRS = 3;
const MATCH_SIZE_RS = 4;
const DEFAULT_EXPIRY_MINS = 30;

// ==========================================
// In-Memory Database & State
// ==========================================
interface QueueEntry {
  id: string;
  userId: string;
  displayName: string;
  serverId: string;
  serverName: string;
  mode: "drs" | "rs";
  level: number;
  joinedAt: string;
  expiresAt: string;
  quickstart: boolean;
  assist: boolean;
  notes?: string;
}

interface TrackedCorp {
  corpId: string;
  corpName: string;
  bonusPct: number | null;
  lastFetched: string | null;
  isActive: boolean;
  fetchError: string | null;
  createdAt: string;
}

interface MatchRecord {
  id: number;
  mode: "drs" | "rs";
  level: number;
  createdAt: string;
  status: "active" | "completed";
  sosNotice?: string | null;
  participants: Array<{
    userId: string;
    displayName: string;
    serverName: string;
    assist: boolean;
  }>;
}

interface IncidentReport {
  id: number;
  matchId: number;
  reporterName: string;
  reportedName: string;
  reason: string;
  details: string;
  status: "open" | "resolved";
  createdAt: string;
  notes?: string;
}

interface ServerInfo {
  guildId: string;
  name: string;
  queueChannelId?: string;
  language: string;
  memberCount: number;
}

// Initial Seed Data
const state = {
  servers: new Map<string, ServerInfo>([
    [
      "536065295828254732",
      {
        guildId: "536065295828254732",
        name: "Dark Red Star Community Hub",
        queueChannelId: "109876543210987654",
        language: "en",
        memberCount: 1420
      }
    ],
    [
      "782394019283746192",
      {
        guildId: "782394019283746192",
        name: "Iron Vanguard Fleet",
        queueChannelId: "209876543210987655",
        language: "en",
        memberCount: 310
      }
    ],
    [
      "918273645102938475",
      {
        guildId: "918273645102938475",
        name: "Nova Prime Syndicate",
        queueChannelId: "309876543210987656",
        language: "ja",
        memberCount: 260
      }
    ]
  ]),

  queues: new Map<string, QueueEntry>([
    [
      "q1",
      {
        id: "q1",
        userId: "508209182374363137",
        displayName: "StarCommander",
        serverId: "536065295828254732",
        serverName: "Dark Red Star Hub",
        mode: "drs",
        level: 11,
        joinedAt: new Date(Date.now() - 6 * 60000).toISOString(),
        expiresAt: new Date(Date.now() + 24 * 60000).toISOString(),
        quickstart: true,
        assist: false,
        notes: "Genesis 12 / ModTRSE"
      }
    ],
    [
      "q2",
      {
        id: "q2",
        userId: "702623662531936356",
        displayName: "AstroValkyrie",
        serverId: "536065295828254732",
        serverName: "Dark Red Star Hub",
        mode: "drs",
        level: 11,
        joinedAt: new Date(Date.now() - 3 * 60000).toISOString(),
        expiresAt: new Date(Date.now() + 27 * 60000).toISOString(),
        quickstart: true,
        assist: false,
        notes: "Enrich 11"
      }
    ],
    [
      "q3",
      {
        id: "q3",
        userId: "670486428743892993",
        displayName: "VoidWalker",
        serverId: "782394019283746192",
        serverName: "Iron Vanguard",
        mode: "rs",
        level: 9,
        joinedAt: new Date(Date.now() - 10 * 60000).toISOString(),
        expiresAt: new Date(Date.now() + 20 * 60000).toISOString(),
        quickstart: false,
        assist: true,
        notes: "Support BS"
      }
    ]
  ]),

  corps: new Map<string, TrackedCorp>([
    [
      "b6e23a3f1f3a3c735c694624b273dcd7da2f8bd13a5ac2b36a8ad39737b1d062",
      {
        corpId: "b6e23a3f1f3a3c735c694624b273dcd7da2f8bd13a5ac2b36a8ad39737b1d062",
        corpName: "Solaris Alliance",
        bonusPct: 56,
        lastFetched: new Date(Date.now() - 25 * 60000).toISOString(),
        isActive: true,
        fetchError: null,
        createdAt: new Date(Date.now() - 86400000).toISOString()
      }
    ],
    [
      "a1c93f0b4d8e7a6c5b4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b",
      {
        corpId: "a1c93f0b4d8e7a6c5b4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b",
        corpName: "Cerberus Void Raiders",
        bonusPct: 48,
        lastFetched: new Date(Date.now() - 40 * 60000).toISOString(),
        isActive: true,
        fetchError: null,
        createdAt: new Date(Date.now() - 172800000).toISOString()
      }
    ],
    [
      "f8e7d6c5b4a39281706f5e4d3c2b1a0987654321fedcba0987654321fedcba09",
      {
        corpId: "f8e7d6c5b4a39281706f5e4d3c2b1a0987654321fedcba0987654321fedcba09",
        corpName: "Nebula Vanguard",
        bonusPct: 42,
        lastFetched: new Date(Date.now() - 55 * 60000).toISOString(),
        isActive: true,
        fetchError: null,
        createdAt: new Date(Date.now() - 259200000).toISOString()
      }
    ]
  ]),

  matches: [
    {
      id: 1042,
      mode: "drs" as const,
      level: 10,
      createdAt: new Date(Date.now() - 15 * 60000).toISOString(),
      status: "active" as const,
      participants: [
        { userId: "101", displayName: "GhostShip", serverName: "DRS Community", assist: false },
        { userId: "102", displayName: "NebulaKnight", serverName: "Nova Prime", assist: false },
        { userId: "103", displayName: "OrionHunter", serverName: "Iron Vanguard", assist: false }
      ]
    },
    {
      id: 1041,
      mode: "rs" as const,
      level: 8,
      createdAt: new Date(Date.now() - 75 * 60000).toISOString(),
      status: "completed" as const,
      participants: [
        { userId: "201", displayName: "Hyperion", serverName: "DRS Community", assist: false },
        { userId: "202", displayName: "ChronoDrift", serverName: "DRS Community", assist: false },
        { userId: "203", displayName: "PulsarX", serverName: "Iron Vanguard", assist: true },
        { userId: "204", displayName: "SolarisAce", serverName: "Nova Prime", assist: false }
      ]
    }
  ] as MatchRecord[],

  reports: [
    {
      id: 501,
      matchId: 1039,
      reporterName: "StarCommander",
      reportedName: "RogueCaptain",
      reason: "AFK during DRS sector clear",
      details: "Player jumped in but remained unresponsive at warp gate for entire 15 min run.",
      status: "resolved" as const,
      createdAt: new Date(Date.now() - 180 * 60000).toISOString(),
      notes: "Player warned by officer team; marked in conduct audit."
    }
  ] as IncidentReport[],

  nextMatchId: 1043,
  nextReportId: 502
};

// ==========================================
// External Corporation Web Scraper (ws.tsl.rocks)
// ==========================================
async function fetchCorpFromWeb(corpId: string): Promise<{ success: boolean; corpName: string | null; bonusPct: number | null; error?: string }> {
  const url = `https://ws.tsl.rocks/corp/${corpId}/`;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 12000);

    const res = await fetch(url, {
      signal: controller.signal,
      headers: {
        "User-Agent": "DRS-Queue-Bot/2.0 (+https://github.com/Sanayajoshi/drs-bot)"
      }
    });
    clearTimeout(timeoutId);

    if (!res.ok) {
      return { success: false, corpName: null, bonusPct: null, error: `HTTP ${res.status}` };
    }

    const html = await res.text();
    const $ = cheerio.load(html);

    // Extract corp name from H1
    let corpName: string | null = $("h1").first().text().trim() || null;

    // Extract bonus percentage
    let bonusPct: number | null = null;
    $("div, p, span, h2, h3").each((_, el) => {
      const text = $(el).text().trim();
      if (text.includes("Bonus") && text.includes("%")) {
        const match = text.match(/Bonus.*?(\d+)%/);
        if (match && match[1]) {
          bonusPct = parseInt(match[1], 10);
          return false; // break loop
        }
      }
    });

    return {
      success: true,
      corpName,
      bonusPct
    };
  } catch (err: any) {
    return {
      success: false,
      corpName: null,
      bonusPct: null,
      error: err.name === "AbortError" ? "Timeout after 12s" : err.message
    };
  }
}

// Background Task: Update Tracked Corp Bonuses Hourly
async function updateAllBonuses() {
  console.log("[Bonus Updater] Running scheduled check for tracked corporation bonuses...");
  for (const [id, corp] of state.corps.entries()) {
    if (!corp.isActive) continue;
    try {
      const result = await fetchCorpFromWeb(id);
      if (result.success && result.bonusPct !== null) {
        corp.bonusPct = result.bonusPct;
        if (result.corpName && !corp.corpName) corp.corpName = result.corpName;
        corp.lastFetched = new Date().toISOString();
        corp.fetchError = null;
      } else if (result.success && result.bonusPct === null) {
        corp.fetchError = "No bonus % detected on page";
        corp.lastFetched = new Date().toISOString();
      } else {
        corp.fetchError = result.error || "Scrape failed";
      }
    } catch (e: any) {
      corp.fetchError = e.message;
    }
  }
}
setInterval(updateAllBonuses, 60 * 60 * 1000); // Hourly

// Automatic Expiry Cleaner for Queues
setInterval(() => {
  const now = new Date();
  for (const [key, item] of state.queues.entries()) {
    if (new Date(item.expiresAt) <= now) {
      state.queues.delete(key);
      console.log(`[Queue] Expired entry ${key} for ${item.displayName} (DRS/RS ${item.level})`);
    }
  }
}, 30 * 1000);

// ==========================================
// Express Web Application
// ==========================================
const app = express();
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Discord Bot Client Setup
let botClient: Client | null = null;
let botIsReady = false;

if (BOT_TOKEN) {
  try {
    botClient = new Client({
      intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
      ]
    });

    botClient.on("ready", () => {
      botIsReady = true;
      console.log(`[Discord Bot] Logged in as ${botClient?.user?.tag} (${botClient?.user?.id})`);
      botClient?.user?.setPresence({
        activities: [{ name: "DRS & RS Queues | /drs", type: ActivityType.Watching }],
        status: "online"
      });

      // Populate guilds in state
      botClient?.guilds.cache.forEach((guild) => {
        state.servers.set(guild.id, {
          guildId: guild.id,
          name: guild.name,
          language: "en",
          memberCount: guild.memberCount
        });
      });
    });

    botClient.on("guildCreate", (guild) => {
      state.servers.set(guild.id, {
        guildId: guild.id,
        name: guild.name,
        language: "en",
        memberCount: guild.memberCount
      });
      console.log(`[Discord Bot] Joined guild: ${guild.name} (${guild.id})`);
    });

    botClient.login(BOT_TOKEN).catch((err) => {
      console.warn(`[Discord Bot] Login failed: ${err.message}. Running web server in standalone mode.`);
    });
  } catch (err: any) {
    console.warn(`[Discord Bot] Initialization error: ${err.message}`);
  }
} else {
  console.log("[Discord Bot] DISCORD_BOT_TOKEN not configured. Web Dashboard active in standalone monitor mode.");
}

// ------------------------------------------
// Health & API Status Endpoints
// ------------------------------------------
app.get(["/health", "/api/health"], (req, res) => {
  res.json({
    status: "healthy",
    bot_connected: botIsReady,
    bot_user: botClient?.user?.tag || null,
    guilds_count: botIsReady ? botClient?.guilds.cache.size : state.servers.size,
    database: "connected"
  });
});

app.get("/api/status", (req, res) => {
  res.json({
    is_ready: botIsReady,
    bot_user: botClient?.user?.tag || null,
    registered_servers: state.servers.size,
    active_queue_entries: state.queues.size,
    discord_token_configured: Boolean(BOT_TOKEN),
    supported_drs_levels: DRS_LEVELS,
    supported_rs_levels: RS_LEVELS
  });
});

// ------------------------------------------
// Queue API
// ------------------------------------------
app.get("/api/queues", (req, res) => {
  const list = Array.from(state.queues.values());
  res.json(list);
});

app.post("/api/queues/join", (req, res) => {
  const { displayName, altName, mode, level, quickstart, assist, notes } = req.body;
  if (!displayName || !mode || !level) {
    return res.status(400).json({ error: "Missing displayName, mode, or level" });
  }

  const validLevels = mode === "drs" ? DRS_LEVELS : RS_LEVELS;
  const numLevel = parseInt(level, 10);
  if (!validLevels.includes(numLevel)) {
    return res.status(400).json({ error: `Invalid level ${numLevel} for mode ${mode}` });
  }

  const cleanAlt = altName && typeof altName === "string" ? altName.trim() : "";
  const effectiveName = cleanAlt && cleanAlt.toLowerCase() !== "main"
    ? `${String(displayName).trim()} (${cleanAlt})`
    : String(displayName).trim();

  const id = `q_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`;
  const now = new Date();
  const entry: QueueEntry = {
    id,
    userId: `sim_${Date.now()}`,
    displayName: effectiveName,
    serverId: "536065295828254732",
    serverName: "Dark Red Star Community Hub",
    mode: mode === "rs" ? "rs" : "drs",
    level: numLevel,
    joinedAt: now.toISOString(),
    expiresAt: new Date(now.getTime() + DEFAULT_EXPIRY_MINS * 60000).toISOString(),
    quickstart: Boolean(quickstart),
    assist: Boolean(assist),
    notes: notes || undefined
  };

  state.queues.set(id, entry);

  // Check if queue triggers match
  const matching = Array.from(state.queues.values()).filter(
    (q) => q.mode === entry.mode && q.level === entry.level
  );

  const targetSize = entry.mode === "drs" ? MATCH_SIZE_DRS : MATCH_SIZE_RS;
  const allQuickstart = matching.length >= 2 && matching.every((m) => m.quickstart);

  if (matching.length >= targetSize || allQuickstart) {
    const matchedPlayers = matching.slice(0, targetSize);
    for (const p of matchedPlayers) {
      state.queues.delete(p.id);
    }

    const sosPlayers = matchedPlayers.filter((p) => p.assist).map((p) => p.displayName);
    const sosNotice = sosPlayers.length > 0
      ? `🆘 Fleet Escort Alert: ${sosPlayers.join(", ")} signed up as SOS and will need a carry!`
      : null;

    const match: MatchRecord = {
      id: state.nextMatchId++,
      mode: entry.mode,
      level: entry.level,
      createdAt: new Date().toISOString(),
      status: "active",
      sosNotice,
      participants: matchedPlayers.map((p) => ({
        userId: p.userId,
        displayName: p.displayName,
        serverName: p.serverName,
        assist: p.assist
      }))
    };
    state.matches.unshift(match);
    return res.json({ success: true, entry, matchCreated: match });
  }

  res.json({ success: true, entry });
});

app.post("/api/queues/leave", (req, res) => {
  const { id } = req.body;
  if (!id || !state.queues.has(id)) {
    return res.status(404).json({ error: "Queue entry not found" });
  }
  state.queues.delete(id);
  res.json({ success: true, message: "Left queue successfully" });
});

app.post("/api/queues/quickstart", (req, res) => {
  const { id } = req.body;
  const entry = state.queues.get(id);
  if (!entry) return res.status(404).json({ error: "Queue entry not found" });

  entry.quickstart = !entry.quickstart;

  // Calculate alert message
  const matching = Array.from(state.queues.values()).filter(
    (q) => q.mode === entry.mode && q.level === entry.level
  );
  const total = entry.mode === "drs" ? MATCH_SIZE_DRS : MATCH_SIZE_RS;
  const current = matching.length;
  const otherPlayers = matching.filter((p) => p.id !== entry.id);

  let alertMessage = "";
  if (current <= 1) {
    alertMessage = `Pilot ${entry.displayName} ready to go 1/${total}`;
  } else {
    const otherNames = otherPlayers.map((p) => `@${p.displayName}`).join(", ");
    alertMessage = `${otherNames}, Pilot ${entry.displayName} ready to go ${current}/${total}, press quickstart to start`;
  }

  res.json({
    success: true,
    quickstart: entry.quickstart,
    message: alertMessage,
    current,
    total
  });
});

// ------------------------------------------
// Corporation Bonuses API
// ------------------------------------------
app.get("/api/corps", (req, res) => {
  const corps = Array.from(state.corps.values()).sort(
    (a, b) => (b.bonusPct ?? -1) - (a.bonusPct ?? -1)
  );
  res.json(corps);
});

app.post("/api/corps", async (req, res) => {
  const { corpId, name } = req.body;
  if (!corpId || typeof corpId !== "string") {
    return res.status(400).json({ error: "Missing corpId" });
  }

  const cleanId = corpId.trim().toLowerCase();
  if (!/^[a-f0-9]{64}$/.test(cleanId)) {
    return res.status(400).json({
      error: "Invalid corporation ID format. Must be exactly 64 hexadecimal characters from ws.tsl.rocks/corp/<id>."
    });
  }

  // Scrape live bonus
  const scraped = await fetchCorpFromWeb(cleanId);
  const corpName = name?.trim() || scraped.corpName || "Tracked Corp";

  const newCorp: TrackedCorp = {
    corpId: cleanId,
    corpName,
    bonusPct: scraped.bonusPct,
    lastFetched: new Date().toISOString(),
    isActive: true,
    fetchError: scraped.success ? (scraped.bonusPct === null ? "No bonus detected on page" : null) : scraped.error || "Fetch failed",
    createdAt: new Date().toISOString()
  };

  state.corps.set(cleanId, newCorp);
  res.json({
    success: true,
    corp: newCorp,
    message: scraped.bonusPct !== null 
      ? `Added ${corpName} with ${scraped.bonusPct}% bonus`
      : `Added ${corpName} (Bonus extraction pending)`
  });
});

app.post("/api/corps/:id/refresh", async (req, res) => {
  const corp = state.corps.get(req.params.id);
  if (!corp) return res.status(404).json({ error: "Corporation not found" });

  const scraped = await fetchCorpFromWeb(corp.corpId);
  if (scraped.success && scraped.bonusPct !== null) {
    corp.bonusPct = scraped.bonusPct;
    if (scraped.corpName) corp.corpName = scraped.corpName;
    corp.lastFetched = new Date().toISOString();
    corp.fetchError = null;
  } else {
    corp.fetchError = scraped.error || "Could not retrieve bonus";
    corp.lastFetched = new Date().toISOString();
  }

  res.json({ success: true, corp });
});

app.delete("/api/corps/:id", (req, res) => {
  if (!state.corps.has(req.params.id)) {
    return res.status(404).json({ error: "Corporation not found" });
  }
  state.corps.delete(req.params.id);
  res.json({ success: true, message: "Removed corporation successfully" });
});

// ------------------------------------------
// Matches & Investigations API
// ------------------------------------------
app.get("/api/matches", (req, res) => {
  res.json(state.matches);
});

app.get("/api/investigations", (req, res) => {
  res.json(state.reports);
});

app.post("/api/investigations/resolve", (req, res) => {
  const { id, notes } = req.body;
  const report = state.reports.find((r) => r.id === parseInt(id, 10));
  if (!report) return res.status(404).json({ error: "Report not found" });

  report.status = "resolved";
  report.notes = notes || "Resolved by officer.";
  res.json({ success: true, report });
});

// ------------------------------------------
// HTML Dashboard Monitor (GET /)
// ------------------------------------------
app.get("/", (req, res) => {
  const isOnline = botIsReady;
  const botUser = botClient?.user?.tag || (BOT_TOKEN ? "Connecting..." : "Standalone Web Monitor (Token Not Set)");
  const serverCount = isOnline ? botClient?.guilds.cache.size : state.servers.size;
  const activeQueuesCount = state.queues.size;
  const corpsCount = state.corps.size;
  const activeMatchesCount = state.matches.filter((m) => m.status === "active").length;

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>DRS Queue Bot Dashboard | Hades' Star</title>
  <meta name="description" content="Multi-server Discord bot and live web monitor for Hades' Star Dark Red Star queues, matchmaking, and player incident investigations.">
  <style>
    :root {
      --bg-main: #0a0e17;
      --bg-card: #111827;
      --bg-card-sub: #1f293d;
      --border-color: #273549;
      --accent-drs: #ef4444;
      --accent-rs: #f59e0b;
      --accent-blue: #3b82f6;
      --accent-green: #10b981;
      --text-main: #f3f4f6;
      --text-muted: #94a3b8;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background: var(--bg-main);
      color: var(--text-main);
      padding: 30px 20px;
      display: flex;
      justify-content: center;
      min-height: 100vh;
    }
    .container {
      max-width: 1060px;
      width: 100%;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--border-color);
      margin-bottom: 28px;
      flex-wrap: wrap;
      gap: 16px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .brand-icon {
      font-size: 2rem;
      background: linear-gradient(135deg, #ef4444, #7f1d1d);
      padding: 8px 12px;
      border-radius: 10px;
      box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
    }
    .brand-title h1 {
      font-size: 1.5rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: #fff;
    }
    .brand-title p {
      font-size: 0.85rem;
      color: var(--text-muted);
    }
    .status-badge {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 14px;
      border-radius: 9999px;
      font-size: 0.825rem;
      font-weight: 600;
    }
    .status-badge.online {
      background: rgba(16, 185, 129, 0.15);
      color: #34d399;
      border: 1px solid rgba(16, 185, 129, 0.4);
    }
    .status-badge.standby {
      background: rgba(245, 158, 11, 0.15);
      color: #fbbf24;
      border: 1px solid rgba(245, 158, 11, 0.4);
    }
    .pulse-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: currentColor;
    }
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 28px;
    }
    .card {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px;
      position: relative;
      overflow: hidden;
    }
    .card::before {
      content: "";
      position: absolute;
      top: 0; left: 0; right: 0; height: 3px;
      background: var(--border-color);
    }
    .card.accent-red::before { background: var(--accent-drs); }
    .card.accent-yellow::before { background: var(--accent-rs); }
    .card.accent-blue::before { background: var(--accent-blue); }
    .card.accent-green::before { background: var(--accent-green); }
    .card-label {
      font-size: 0.775rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      margin-bottom: 6px;
    }
    .card-value {
      font-size: 1.75rem;
      font-weight: 700;
      color: #fff;
    }
    .card-subtext {
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 4px;
    }
    .section-title {
      font-size: 1.15rem;
      font-weight: 600;
      margin: 28px 0 16px;
      color: #f1f5f9;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .interactive-panel {
      background: var(--bg-card);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 24px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.875rem;
    }
    th, td {
      padding: 12px 14px;
      text-align: left;
      border-bottom: 1px solid var(--border-color);
    }
    th {
      background: var(--bg-card-sub);
      color: var(--text-muted);
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    tr:last-child td { border-bottom: none; }
    .tag {
      display: inline-block;
      padding: 3px 8px;
      border-radius: 4px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .tag.drs { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .tag.rs { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .tag.bonus { background: rgba(16, 185, 129, 0.2); color: #34d399; font-weight: 700; }
    .btn {
      background: #2563eb;
      color: #fff;
      border: none;
      padding: 8px 14px;
      border-radius: 6px;
      font-size: 0.825rem;
      cursor: pointer;
      font-weight: 500;
      transition: background 0.15s;
    }
    .btn:hover { background: #1d4ed8; }
    .btn-secondary { background: #374151; color: #e5e7eb; }
    .btn-secondary:hover { background: #4b5563; }
    .btn-danger { background: #dc2626; }
    .btn-danger:hover { background: #b91c1c; }
    .btn-sm { padding: 4px 8px; font-size: 0.75rem; }
    .input-group {
      display: flex;
      gap: 10px;
      margin-top: 14px;
      flex-wrap: wrap;
    }
    input, select {
      background: #1e293b;
      border: 1px solid #334155;
      color: #fff;
      padding: 8px 12px;
      border-radius: 6px;
      font-size: 0.85rem;
    }
    input:focus, select:focus {
      outline: 2px solid #3b82f6;
    }
    .instructions-box {
      background: #0f172a;
      border-left: 4px solid var(--accent-blue);
      padding: 16px 20px;
      border-radius: 0 8px 8px 0;
      font-size: 0.875rem;
      line-height: 1.6;
      color: #cbd5e1;
      margin-top: 24px;
    }
    .instructions-box code {
      background: #1e293b;
      padding: 2px 6px;
      border-radius: 4px;
      color: #93c5fd;
      font-family: monospace;
    }
    .flex-between {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="brand">
        <div class="brand-icon">☄️</div>
        <div class="brand-title">
          <h1>DRS Queue Bot Dashboard</h1>
          <p>Hades' Star Dark Red Star Multi-Server Matchmaking & Incident Monitor</p>
        </div>
      </div>
      <div>
        <span class="status-badge ${isOnline ? "online" : "standby"}">
          <span class="pulse-dot"></span>
          ${isOnline ? "Discord Connected" : "Standalone Web Monitor"}
        </span>
      </div>
    </header>

    <div class="stats-grid">
      <div class="card accent-red">
        <div class="card-label">Active Queue Players</div>
        <div class="card-value" id="stat-queues">${activeQueuesCount}</div>
        <div class="card-subtext">DRS (7-12) & RS (4-12)</div>
      </div>
      <div class="card accent-blue">
        <div class="card-label">Configured Servers</div>
        <div class="card-value" id="stat-servers">${serverCount}</div>
        <div class="card-subtext">Registered Guilds</div>
      </div>
      <div class="card accent-green">
        <div class="card-label">Tracked Corps</div>
        <div class="card-value" id="stat-corps">${corpsCount}</div>
        <div class="card-subtext">Hourly Auto-Scraped Bonuses</div>
      </div>
      <div class="card accent-yellow">
        <div class="card-label">Active Matches</div>
        <div class="card-value" id="stat-matches">${activeMatchesCount}</div>
        <div class="card-subtext">Dispatching in progress</div>
      </div>
    </div>

    <!-- Live Queue Section -->
    <div class="section-title">
      <span>🚀 Live Queues Monitor</span>
      <span style="font-size: 0.8rem; color: var(--text-muted);">Real-time dispatch state</span>
    </div>
    <div class="interactive-panel">
      <div style="overflow-x: auto;">
        <table id="queues-table">
          <thead>
            <tr>
              <th>Player</th>
              <th>Server</th>
              <th>Mode / Level</th>
              <th>Quickstart</th>
              <th>Assist</th>
              <th>Notes / Ship Tech</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="queues-body">
            <tr><td colspan="7" style="text-align: center; color: var(--text-muted);">Loading active queues...</td></tr>
          </tbody>
        </table>
      </div>

      <!-- Queue Join Simulator -->
      <div style="margin-top: 18px; padding-top: 16px; border-top: 1px solid var(--border-color);">
        <div style="font-size: 0.85rem; font-weight: 600; color: #94a3b8; margin-bottom: 8px;">Enqueue Pilot Simulation:</div>
        <form id="join-form" class="input-group" onsubmit="handleJoinQueue(event)">
          <input type="text" id="join-name" placeholder="Pilot Call-sign (e.g. NovaPilot)" required style="flex: 2; min-width: 140px;">
          <input type="text" id="join-alt" placeholder="Alt Name (e.g. Alt 1, optional)" style="flex: 1.5; min-width: 120px;">
          <select id="join-mode" style="flex: 1; min-width: 90px;" onchange="updateLevelsDropdown()">
            <option value="drs">DRS (Dark Red Star)</option>
            <option value="rs">RS (Red Star)</option>
          </select>
          <select id="join-level" style="flex: 1; min-width: 80px;">
            <option value="7">Level 7</option>
            <option value="8">Level 8</option>
            <option value="9">Level 9</option>
            <option value="10">Level 10</option>
            <option value="11" selected>Level 11</option>
            <option value="12">Level 12</option>
          </select>
          <input type="text" id="join-notes" placeholder="Notes (Genesis, Enrich...)" style="flex: 2; min-width: 130px;">
          <label style="display: flex; align-items: center; gap: 5px; font-size: 0.8rem; color: #94a3b8;">
            <input type="checkbox" id="join-qs"> Quickstart
          </label>
          <label style="display: flex; align-items: center; gap: 5px; font-size: 0.8rem; color: #ef4444; font-weight: 600;">
            <input type="checkbox" id="join-assist"> 🆘 SOS (Need Carry)
          </label>
          <button type="submit" class="btn">+ Enqueue Pilot</button>
        </form>
      </div>
    </div>

    <!-- Corporation Bonuses Section -->
    <div class="section-title">
      <span>🏢 Corporation Bonus Percentage Tracker</span>
      <span style="font-size: 0.8rem; color: var(--text-muted);">Scraped from ws.tsl.rocks</span>
    </div>
    <div class="interactive-panel">
      <div style="overflow-x: auto;">
        <table id="corps-table">
          <thead>
            <tr>
              <th>Corporation Name</th>
              <th>Bonus %</th>
              <th>TSL Corp ID (64-hex)</th>
              <th>Last Checked</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody id="corps-body">
            <tr><td colspan="6" style="text-align: center; color: var(--text-muted);">Loading corporations...</td></tr>
          </tbody>
        </table>
      </div>

      <!-- Add Corp Form -->
      <div style="margin-top: 18px; padding-top: 16px; border-top: 1px solid var(--border-color);">
        <div style="font-size: 0.85rem; font-weight: 600; color: #94a3b8; margin-bottom: 8px;">Track New Corporation from TSL:</div>
        <form id="add-corp-form" class="input-group" onsubmit="handleAddCorp(event)">
          <input type="text" id="corp-id" placeholder="64-hex Corporation ID from ws.tsl.rocks/corp/<id>" required style="flex: 3; min-width: 250px;">
          <input type="text" id="corp-name" placeholder="Optional Name Override" style="flex: 2; min-width: 150px;">
          <button type="submit" class="btn">+ Track Corporation</button>
        </form>
      </div>
    </div>

    <!-- Recent Matches & Runs -->
    <div class="section-title">
      <span>⚔️ Recent Dispatched Matches</span>
    </div>
    <div class="interactive-panel">
      <div style="overflow-x: auto;">
        <table>
          <thead>
            <tr>
              <th>Match ID</th>
              <th>Type / Tier</th>
              <th>Dispatched</th>
              <th>Status</th>
              <th>Pilots Dispatched</th>
            </tr>
          </thead>
          <tbody id="matches-body">
            <tr><td colspan="5" style="text-align: center; color: var(--text-muted);">Loading matches...</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Discord Bot Configuration Guide -->
    <div class="instructions-box">
      <strong>🤖 Connecting Your Discord Bot:</strong><br>
      The web server is up and listening on port <code>${PORT}</code>.
      ${BOT_TOKEN ? `<span style="color:#34d399;">✓ DISCORD_BOT_TOKEN is active. Logged in as <code>${botUser}</code>.</span>` : `To connect this bot to your Discord servers, open workspace <strong>Settings &gt; Environment Variables</strong>, set <code>DISCORD_BOT_TOKEN</code> to your Discord Bot Token from the Discord Developer Portal, and save.`}
      <br>
      Available Slash Commands: <code>/drs</code> (queue interface), <code>/officer bonus_set</code>, <code>/add_corporation</code>, <code>/list_corporations</code>, <code>/stats</code>, <code>/feedback</code>.
    </div>
  </div>

  <script>
    async function loadQueues() {
      try {
        const res = await fetch('/api/queues');
        const queues = await res.json();
        const tbody = document.getElementById('queues-body');
        document.getElementById('stat-queues').innerText = queues.length;
        if (!queues.length) {
          tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 24px;">No pilots currently waiting in queue. Use the form below to queue a pilot!</td></tr>';
          return;
        }
        tbody.innerHTML = queues.map(q => \`
          <tr>
            <td><strong>\${escapeHtml(q.displayName)}</strong></td>
            <td>\${escapeHtml(q.serverName)}</td>
            <td><span class="tag \${q.mode}">\${q.mode.toUpperCase()} \${q.level}</span></td>
            <td>\${q.quickstart ? '<span style="color:#34d399;">▶️ Yes</span>' : '<span style="color:#94a3b8;">No</span>'}</td>
            <td>\${q.assist ? '<span style="color:#fbbf24;">🆘 Assist</span>' : '<span style="color:#94a3b8;">—</span>'}</td>
            <td>\${escapeHtml(q.notes || '—')}</td>
            <td>
              <button class="btn btn-secondary btn-sm" onclick="toggleQuickstart('\${q.id}')">Toggle QS</button>
              <button class="btn btn-danger btn-sm" onclick="leaveQueue('\${q.id}')">Leave</button>
            </td>
          </tr>
        \`).join('');
      } catch (e) {
        console.error(e);
      }
    }

    async function loadCorps() {
      try {
        const res = await fetch('/api/corps');
        const corps = await res.json();
        const tbody = document.getElementById('corps-body');
        document.getElementById('stat-corps').innerText = corps.length;
        if (!corps.length) {
          tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 20px;">No corporations tracked yet.</td></tr>';
          return;
        }
        tbody.innerHTML = corps.map(c => \`
          <tr>
            <td><strong>\${escapeHtml(c.corpName)}</strong></td>
            <td>\${c.bonusPct !== null ? \`<span class="tag bonus">\${c.bonusPct}% Bonus</span>\` : '<span style="color:#f87171;">Pending / 0%</span>'}</td>
            <td><code style="font-size:0.75rem; color:#94a3b8;">\${c.corpId.substring(0, 16)}...</code></td>
            <td style="font-size:0.8rem; color:#94a3b8;">\${c.lastFetched ? new Date(c.lastFetched).toLocaleTimeString() : 'Never'}</td>
            <td>\${c.fetchError ? \`<span style="color:#f87171; font-size:0.75rem;">\${escapeHtml(c.fetchError)}</span>\` : '<span style="color:#34d399; font-size:0.75rem;">✓ Active</span>'}</td>
            <td>
              <button class="btn btn-secondary btn-sm" onclick="refreshCorp('\${c.corpId}')">Refresh</button>
              <button class="btn btn-danger btn-sm" onclick="deleteCorp('\${c.corpId}')">Remove</button>
            </td>
          </tr>
        \`).join('');
      } catch (e) {
        console.error(e);
      }
    }

    async function loadMatches() {
      try {
        const res = await fetch('/api/matches');
        const matches = await res.json();
        const tbody = document.getElementById('matches-body');
        document.getElementById('stat-matches').innerText = matches.filter(m => m.status === 'active').length;
        if (!matches.length) {
          tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted); padding: 20px;">No recent matches recorded yet.</td></tr>';
          return;
        }
        tbody.innerHTML = matches.map(m => \`
          <tr>
            <td><strong>#\${m.id}</strong></td>
            <td><span class="tag \${m.mode}">\${m.mode.toUpperCase()} \${m.level}</span></td>
            <td style="font-size:0.8rem; color:#94a3b8;">\${new Date(m.createdAt).toLocaleTimeString()}</td>
            <td><span style="color: \${m.status === 'active' ? '#34d399' : '#94a3b8'};">\${m.status.toUpperCase()}</span></td>
            <td style="font-size:0.85rem;">
              <div>\${m.participants.map(p => escapeHtml(p.displayName) + (p.assist ? ' <span style="color:#ef4444; font-weight:700;">🆘</span>' : '')).join(', ')}</div>
              \${m.sosNotice ? \`<div style="margin-top:4px; font-size:0.75rem; color:#f87171; background:rgba(239,68,68,0.15); border:1px solid rgba(239,68,68,0.3); padding:3px 8px; border-radius:4px; display:inline-block;">\${escapeHtml(m.sosNotice)}</div>\` : ''}
            </td>
          </tr>
        \`).join('');
      } catch (e) {
        console.error(e);
      }
    }

    function updateLevelsDropdown() {
      const mode = document.getElementById('join-mode').value;
      const select = document.getElementById('join-level');
      select.innerHTML = '';
      const levels = mode === 'drs' ? [7, 8, 9, 10, 11, 12] : [4, 5, 6, 7, 8, 9, 10, 11, 12];
      levels.forEach(lvl => {
        const opt = document.createElement('option');
        opt.value = lvl;
        opt.textContent = 'Level ' + lvl;
        if (lvl === 11) opt.selected = true;
        select.appendChild(opt);
      });
    }

    function showToast(msg) {
      let toast = document.getElementById('live-toast');
      if (!toast) {
        toast = document.createElement('div');
        toast.id = 'live-toast';
        toast.style.cssText = 'position:fixed; bottom:24px; right:24px; background:#1e293b; color:#f1f5f9; border-left:4px solid #3b82f6; padding:12px 18px; border-radius:6px; box-shadow:0 8px 24px rgba(0,0,0,0.5); z-index:9999; font-size:0.875rem; transition:opacity 0.2s;';
        document.body.appendChild(toast);
      }
      toast.innerText = msg;
      toast.style.opacity = '1';
      setTimeout(() => { toast.style.opacity = '0'; }, 5000);
    }

    async function handleJoinQueue(e) {
      e.preventDefault();
      const displayName = document.getElementById('join-name').value;
      const altName = document.getElementById('join-alt').value;
      const mode = document.getElementById('join-mode').value;
      const level = document.getElementById('join-level').value;
      const notes = document.getElementById('join-notes').value;
      const quickstart = document.getElementById('join-qs').checked;
      const assist = document.getElementById('join-assist').checked;

      const res = await fetch('/api/queues/join', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ displayName, altName, mode, level, notes, quickstart, assist })
      });
      const data = await res.json();
      if (data.success) {
        document.getElementById('join-name').value = '';
        document.getElementById('join-alt').value = '';
        document.getElementById('join-notes').value = '';
        document.getElementById('join-assist').checked = false;
        loadQueues();
        loadMatches();
        if (data.matchCreated && data.matchCreated.sosNotice) {
          showToast(data.matchCreated.sosNotice);
        }
      } else {
        alert(data.error || 'Failed to join queue');
      }
    }

    async function leaveQueue(id) {
      await fetch('/api/queues/leave', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      });
      loadQueues();
    }

    async function toggleQuickstart(id) {
      const res = await fetch('/api/queues/quickstart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id })
      });
      const data = await res.json();
      if (data.success && data.message) {
        showToast(data.message);
      }
      loadQueues();
    }

    async function handleAddCorp(e) {
      e.preventDefault();
      const corpId = document.getElementById('corp-id').value;
      const name = document.getElementById('corp-name').value;
      const btn = e.target.querySelector('button');
      btn.innerText = 'Fetching...';
      btn.disabled = true;

      try {
        const res = await fetch('/api/corps', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ corpId, name })
        });
        const data = await res.json();
        if (data.success) {
          document.getElementById('corp-id').value = '';
          document.getElementById('corp-name').value = '';
          loadCorps();
        } else {
          alert(data.error || 'Failed to track corporation');
        }
      } catch (err) {
        alert('Network error while scraping corporation');
      } finally {
        btn.innerText = '+ Track Corporation';
        btn.disabled = false;
      }
    }

    async function refreshCorp(id) {
      await fetch('/api/corps/' + id + '/refresh', { method: 'POST' });
      loadCorps();
    }

    async function deleteCorp(id) {
      if (!confirm('Stop tracking this corporation?')) return;
      await fetch('/api/corps/' + id, { method: 'DELETE' });
      loadCorps();
    }

    function escapeHtml(str) {
      if (!str) return '';
      return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
    }

    loadQueues();
    loadCorps();
    loadMatches();
    setInterval(() => {
      loadQueues();
      loadMatches();
    }, 8000);
  </script>
</body>
</html>`;

  res.send(html);
});

// Start Express Server
app.listen(PORT, "0.0.0.0", () => {
  console.log(`[DRS Bot] Web server listening on http://0.0.0.0:${PORT}`);
});
