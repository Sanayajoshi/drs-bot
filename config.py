import os

# Bot token — set in .env or environment
BOT_TOKEN = os.getenv("TOKEN")

# SQLite database file path
DB_PATH = os.getenv("DB_PATH", "drs_bot.db")

# Queue settings
QUEUE_SIZE         = 2
MATCH_SIZE         = 3
DRS_LEVELS = [7, 8, 9, 10, 11, 12]
DEFAULT_QUEUE_MINS = 30
EXTEND_MINS        = 30

# Background task intervals (seconds)
EXPIRY_INTERVAL_SECS = 30

# Feedback delay after match creation
FEEDBACK_DELAY_MINS = 30

# Supported languages
SUPPORTED_LANGUAGES = ["en", "ja", "es", "de", "hi", "pl", "fr"]

# Developer Discord user IDs — always have full bot access
DEV_USER_IDS = [508209182374363137]
