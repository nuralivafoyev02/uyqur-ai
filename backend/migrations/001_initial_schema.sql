create extension if not exists pgcrypto;

create table if not exists admin_users (
  id uuid primary key default gen_random_uuid(),
  username text not null,
  username_normalized text generated always as (lower(username)) stored,
  display_name text not null,
  password_hash text not null,
  must_change_password boolean not null default true,
  is_bootstrap boolean not null default false,
  is_active boolean not null default true,
  last_login_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists idx_admin_users_username_normalized
  on admin_users (username_normalized);

create table if not exists admin_sessions (
  id uuid primary key default gen_random_uuid(),
  admin_user_id uuid not null references admin_users(id) on delete cascade,
  token_hash text not null,
  ip_address text,
  user_agent text,
  expires_at timestamptz not null,
  revoked_at timestamptz,
  last_seen_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create unique index if not exists idx_admin_sessions_token_hash
  on admin_sessions (token_hash);
create index if not exists idx_admin_sessions_user_active
  on admin_sessions (admin_user_id, expires_at desc);

create table if not exists bot_settings (
  key text primary key,
  value_json jsonb not null,
  updated_by_admin_user_id uuid references admin_users(id) on delete set null,
  updated_at timestamptz not null default now()
);

create table if not exists telegram_groups (
  id uuid primary key default gen_random_uuid(),
  chat_id bigint not null,
  title text not null,
  username text,
  group_type text not null check (group_type in ('support', 'management')),
  is_active boolean not null default true,
  is_forum boolean not null default false,
  last_seen_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists idx_telegram_groups_chat_id
  on telegram_groups (chat_id);

create table if not exists agents (
  id uuid primary key default gen_random_uuid(),
  display_name text not null,
  telegram_username text,
  telegram_username_normalized text generated always as (lower(coalesce(telegram_username, ''))) stored,
  telegram_chat_id bigint,
  role text not null default 'agent' check (role in ('agent', 'manager', 'admin')),
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists idx_agents_username_normalized
  on agents (telegram_username_normalized)
  where telegram_username is not null;

create unique index if not exists idx_agents_chat_id
  on agents (telegram_chat_id)
  where telegram_chat_id is not null;

create table if not exists customers (
  id uuid primary key default gen_random_uuid(),
  telegram_user_id bigint not null,
  username text,
  full_name text not null,
  language text not null default 'uz',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists idx_customers_telegram_user_id
  on customers (telegram_user_id);

create table if not exists tickets (
  id uuid primary key default gen_random_uuid(),
  group_id uuid not null references telegram_groups(id) on delete restrict,
  topic_id bigint,
  customer_id uuid not null references customers(id) on delete restrict,
  status text not null check (status in ('open', 'answered', 'closed', 'reopened', 'auto_replied')),
  source_message_id bigint not null,
  source_chat_id bigint not null,
  source_message_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  first_response_at timestamptz,
  first_response_seconds integer,
  closed_at timestamptz,
  closed_reason text,
  closed_by_agent_id uuid references agents(id) on delete set null,
  auto_replied_at timestamptz,
  auto_reply_confidence numeric(5,4),
  last_customer_message_at timestamptz not null default now(),
  last_agent_reply_at timestamptz,
  latest_customer_message_id bigint,
  latest_customer_message_text text,
  reopened_count integer not null default 0
);

create index if not exists idx_tickets_group_status
  on tickets (group_id, status, created_at desc);
create index if not exists idx_tickets_customer_window
  on tickets (group_id, customer_id, topic_id, created_at desc);
create index if not exists idx_tickets_auto_reply_scan
  on tickets (status, auto_replied_at, last_agent_reply_at, created_at);

create table if not exists ticket_messages (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid not null references tickets(id) on delete cascade,
  chat_id bigint not null,
  telegram_message_id bigint not null,
  sender_type text not null check (sender_type in ('customer', 'agent', 'bot', 'system')),
  sender_agent_id uuid references agents(id) on delete set null,
  user_id bigint,
  username text,
  full_name text not null,
  text_content text not null default '',
  normalized_text text not null default '',
  message_type text not null default 'text',
  reply_to_message_id bigint,
  topic_id bigint,
  created_at timestamptz not null,
  raw_payload jsonb
);

create unique index if not exists idx_ticket_messages_unique_telegram
  on ticket_messages (chat_id, telegram_message_id);
create index if not exists idx_ticket_messages_ticket_id
  on ticket_messages (ticket_id, created_at asc);

create table if not exists ticket_events (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid not null references tickets(id) on delete cascade,
  event_type text not null,
  actor_type text not null,
  actor_id text,
  summary text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_ticket_events_ticket_id
  on ticket_events (ticket_id, created_at desc);

create table if not exists kb_entries (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  language text not null default 'uz',
  category text not null,
  answer_template text not null,
  priority integer not null default 10,
  is_active boolean not null default true,
  confidence_threshold_override numeric(5,4),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_kb_entries_active_language
  on kb_entries (is_active, language, priority desc);

create table if not exists kb_terms (
  id uuid primary key default gen_random_uuid(),
  kb_entry_id uuid not null references kb_entries(id) on delete cascade,
  term_type text not null check (term_type in ('keyword', 'synonym', 'pattern')),
  term_value text not null,
  normalized_term text generated always as (lower(term_value)) stored,
  created_at timestamptz not null default now()
);

create unique index if not exists idx_kb_terms_unique
  on kb_terms (kb_entry_id, term_type, normalized_term);
create index if not exists idx_kb_terms_lookup
  on kb_terms (term_type, normalized_term);

create table if not exists auto_reply_logs (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid not null references tickets(id) on delete cascade,
  kb_entry_id uuid references kb_entries(id) on delete set null,
  confidence numeric(5,4) not null,
  response_text text not null,
  fallback_used boolean not null default false,
  match_reasons jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_auto_reply_logs_ticket_id
  on auto_reply_logs (ticket_id, created_at desc);

create table if not exists processed_updates (
  update_id bigint primary key,
  update_hash text,
  received_at timestamptz not null default now()
);

create table if not exists management_reports (
  id uuid primary key default gen_random_uuid(),
  report_type text not null check (report_type in ('hourly', 'daily', 'alert')),
  window_start timestamptz not null,
  window_end timestamptz not null,
  chat_id bigint not null,
  message_text text,
  sent_at timestamptz,
  is_success boolean not null default false,
  error_text text,
  created_at timestamptz not null default now()
);

create unique index if not exists idx_management_reports_unique_window
  on management_reports (report_type, window_start, window_end, chat_id);

create table if not exists audit_logs (
  id uuid primary key default gen_random_uuid(),
  actor_type text not null,
  actor_id text,
  action text not null,
  entity_type text,
  entity_id text,
  metadata jsonb not null default '{}'::jsonb,
  ip_address text,
  created_at timestamptz not null default now()
);

create index if not exists idx_audit_logs_created_at
  on audit_logs (created_at desc);

create table if not exists command_logs (
  id uuid primary key default gen_random_uuid(),
  chat_id bigint not null,
  telegram_user_id bigint,
  command text not null,
  args jsonb not null default '[]'::jsonb,
  was_authorized boolean not null default false,
  response_summary text,
  created_at timestamptz not null default now()
);

create index if not exists idx_command_logs_created_at
  on command_logs (created_at desc);

create table if not exists error_logs (
  id uuid primary key default gen_random_uuid(),
  scope text not null,
  message text not null,
  context jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_error_logs_created_at
  on error_logs (created_at desc);

create table if not exists auth_rate_limits (
  key text primary key,
  attempts integer not null default 0,
  first_attempt_at timestamptz not null default now(),
  blocked_until timestamptz,
  updated_at timestamptz not null default now()
);

create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_admin_users_updated_at on admin_users;
create trigger trg_admin_users_updated_at
before update on admin_users
for each row execute function set_updated_at();

drop trigger if exists trg_bot_settings_updated_at on bot_settings;
create trigger trg_bot_settings_updated_at
before update on bot_settings
for each row execute function set_updated_at();

drop trigger if exists trg_telegram_groups_updated_at on telegram_groups;
create trigger trg_telegram_groups_updated_at
before update on telegram_groups
for each row execute function set_updated_at();

drop trigger if exists trg_agents_updated_at on agents;
create trigger trg_agents_updated_at
before update on agents
for each row execute function set_updated_at();

drop trigger if exists trg_customers_updated_at on customers;
create trigger trg_customers_updated_at
before update on customers
for each row execute function set_updated_at();

drop trigger if exists trg_tickets_updated_at on tickets;
create trigger trg_tickets_updated_at
before update on tickets
for each row execute function set_updated_at();

drop trigger if exists trg_kb_entries_updated_at on kb_entries;
create trigger trg_kb_entries_updated_at
before update on kb_entries
for each row execute function set_updated_at();

drop trigger if exists trg_auth_rate_limits_updated_at on auth_rate_limits;
create trigger trg_auth_rate_limits_updated_at
before update on auth_rate_limits
for each row execute function set_updated_at();

alter table admin_users enable row level security;
alter table admin_sessions enable row level security;
alter table bot_settings enable row level security;
alter table telegram_groups enable row level security;
alter table agents enable row level security;
alter table customers enable row level security;
alter table tickets enable row level security;
alter table ticket_messages enable row level security;
alter table ticket_events enable row level security;
alter table kb_entries enable row level security;
alter table kb_terms enable row level security;
alter table auto_reply_logs enable row level security;
alter table processed_updates enable row level security;
alter table management_reports enable row level security;
alter table audit_logs enable row level security;
alter table command_logs enable row level security;
alter table error_logs enable row level security;
alter table auth_rate_limits enable row level security;
