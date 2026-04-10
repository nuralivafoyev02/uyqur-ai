DEFAULT_TIMEZONE = "Asia/Tashkent"

DEFAULT_SAFE_FALLBACK_MESSAGE = (
    "Assalomu alaykum. So'rovingiz qabul qilindi. Operator tez orada javob beradi."
)

DEFAULT_COMMAND_HELP = """\
/help - mavjud buyruqlar ro'yxati
/stats - joriy umumiy ko'rsatkichlar
/stats_today - bugungi statistika
/stats_week - haftalik statistika
/groupstats - guruhlar bo'yicha kesim
/agentstats - agentlar bo'yicha kesim
/open - ochiq murojaatlar ro'yxati
/registerme - agent chat_id ni biriktirish
"""

LOGIN_RATE_LIMIT_ATTEMPTS = 5
LOGIN_RATE_LIMIT_WINDOW_MINUTES = 15
SESSION_TTL_HOURS = 12
AUTO_REPLY_DELAY_MINUTES = 5
TICKET_MERGE_WINDOW_MINUTES = 30
TICKET_REOPEN_WINDOW_MINUTES = 60
AUTO_REPLY_CONFIDENCE_THRESHOLD = 0.62

BOT_CONTROL_SETTINGS = {
    "auto_reply_enabled",
    "management_hourly_digest_enabled",
    "management_daily_summary_enabled",
    "management_alert_on_sla_breach",
    "safe_fallback_message",
    "default_language",
    "response_merge_window_minutes",
    "reopen_window_minutes",
    "auto_reply_delay_minutes",
    "auto_reply_confidence_threshold",
    "timezone",
    "hourly_digest_cron",
    "daily_summary_cron",
    "management_group_chat_id",
}
