insert into bot_settings(key, value_json)
values
  ('auto_reply_enabled', 'true'::jsonb),
  ('management_hourly_digest_enabled', 'true'::jsonb),
  ('management_daily_summary_enabled', 'true'::jsonb),
  ('management_alert_on_sla_breach', 'true'::jsonb),
  ('auto_reply_delay_minutes', '5'::jsonb),
  ('response_merge_window_minutes', '30'::jsonb),
  ('reopen_window_minutes', '60'::jsonb),
  ('auto_reply_confidence_threshold', '0.62'::jsonb),
  ('safe_fallback_message', to_jsonb('Assalomu alaykum. So''rovingiz qabul qilindi. Operator tez orada javob beradi.'::text)),
  ('default_language', to_jsonb('uz'::text)),
  ('timezone', to_jsonb('Asia/Tashkent'::text)),
  ('hourly_digest_cron', to_jsonb('0 * * * *'::text)),
  ('daily_summary_cron', to_jsonb('0 19 * * *'::text))
on conflict (key) do nothing;
