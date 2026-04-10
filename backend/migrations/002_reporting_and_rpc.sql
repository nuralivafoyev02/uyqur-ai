create or replace function claim_processed_update(p_update_id bigint, p_update_hash text default null)
returns boolean
language plpgsql
security definer
as $$
declare
  inserted_count integer;
begin
  insert into processed_updates(update_id, update_hash)
  values (p_update_id, p_update_hash)
  on conflict do nothing;

  get diagnostics inserted_count = row_count;
  return inserted_count = 1;
end;
$$;

create or replace function claim_management_report(
  p_report_type text,
  p_window_start timestamptz,
  p_window_end timestamptz,
  p_chat_id bigint
)
returns uuid
language plpgsql
security definer
as $$
declare
  report_id uuid;
begin
  insert into management_reports(report_type, window_start, window_end, chat_id)
  values (p_report_type, p_window_start, p_window_end, p_chat_id)
  on conflict (report_type, window_start, window_end, chat_id) do nothing
  returning id into report_id;

  return report_id;
end;
$$;

create or replace function mark_management_report_sent(
  p_report_id uuid,
  p_message_text text,
  p_success boolean,
  p_error_text text default null
)
returns void
language plpgsql
security definer
as $$
begin
  update management_reports
     set message_text = p_message_text,
         is_success = p_success,
         error_text = p_error_text,
         sent_at = case when p_success then now() else sent_at end
   where id = p_report_id;
end;
$$;

create or replace function expire_admin_sessions()
returns integer
language plpgsql
security definer
as $$
declare
  expired_count integer;
begin
  update admin_sessions
     set revoked_at = now()
   where revoked_at is null
     and expires_at < now();

  get diagnostics expired_count = row_count;
  return expired_count;
end;
$$;

create or replace function auth_rate_limit_hit(p_key text)
returns table (
  attempts integer,
  blocked_until timestamptz
)
language plpgsql
security definer
as $$
begin
  return query
  select a.attempts, a.blocked_until
    from auth_rate_limits a
   where a.key = p_key;
end;
$$;

create or replace function auth_rate_limit_fail(
  p_key text,
  p_window_minutes integer default 15,
  p_max_attempts integer default 5
)
returns table (
  attempts integer,
  blocked_until timestamptz
)
language plpgsql
security definer
as $$
declare
  current_row auth_rate_limits%rowtype;
  new_attempts integer;
  new_first_attempt timestamptz;
  new_blocked_until timestamptz;
begin
  select * into current_row
    from auth_rate_limits
   where key = p_key
   for update;

  if not found then
    insert into auth_rate_limits(key, attempts, first_attempt_at)
    values (p_key, 1, now())
    returning * into current_row;
  else
    if current_row.first_attempt_at < now() - make_interval(mins => p_window_minutes) then
      new_attempts := 1;
      new_first_attempt := now();
    else
      new_attempts := current_row.attempts + 1;
      new_first_attempt := current_row.first_attempt_at;
    end if;

    if new_attempts >= p_max_attempts then
      new_blocked_until := now() + make_interval(mins => p_window_minutes);
    else
      new_blocked_until := current_row.blocked_until;
    end if;

    update auth_rate_limits
       set attempts = new_attempts,
           first_attempt_at = new_first_attempt,
           blocked_until = new_blocked_until
     where key = p_key
     returning * into current_row;
  end if;

  return query
  select current_row.attempts, current_row.blocked_until;
end;
$$;

create or replace function auth_rate_limit_reset(p_key text)
returns void
language plpgsql
security definer
as $$
begin
  delete from auth_rate_limits where key = p_key;
end;
$$;

create or replace function stale_open_tickets(p_cutoff timestamptz)
returns table (
  ticket_id uuid,
  group_id uuid,
  group_chat_id bigint,
  group_title text,
  topic_id bigint,
  customer_id uuid,
  customer_name text,
  customer_username text,
  latest_message_id bigint,
  latest_message_text text,
  latest_message_normalized text,
  latest_message_created_at timestamptz
)
language sql
security definer
as $$
  select
    t.id,
    t.group_id,
    g.chat_id,
    g.title,
    t.topic_id,
    t.customer_id,
    c.full_name,
    c.username,
    tm.telegram_message_id,
    tm.text_content,
    tm.normalized_text,
    tm.created_at
  from tickets t
  join telegram_groups g on g.id = t.group_id
  join customers c on c.id = t.customer_id
  left join lateral (
    select *
      from ticket_messages tm
     where tm.ticket_id = t.id
       and tm.sender_type = 'customer'
     order by tm.created_at desc
     limit 1
  ) tm on true
  where t.status in ('open', 'reopened')
    and t.last_agent_reply_at is null
    and t.auto_replied_at is null
    and t.last_customer_message_at <= p_cutoff
    and g.group_type = 'support'
    and g.is_active = true;
$$;

create or replace function stats_overview(
  p_from timestamptz,
  p_to timestamptz
)
returns jsonb
language sql
security definer
as $$
  with base as (
    select *
      from tickets
     where created_at >= p_from
       and created_at < p_to
  ),
  groups as (
    select coalesce(jsonb_agg(row_to_json(x) order by x.total_requests desc), '[]'::jsonb) as payload
      from (
        select
          g.id,
          g.title,
          g.chat_id,
          count(*)::int as total_requests,
          count(*) filter (where t.status in ('open', 'reopened'))::int as open_requests,
          count(*) filter (where t.status = 'closed')::int as closed_requests,
          count(*) filter (where t.auto_replied_at is not null)::int as auto_replied_requests,
          round(
            100.0 * count(*) filter (where t.first_response_at is not null or t.auto_replied_at is not null)
            / nullif(count(*), 0),
            2
          ) as response_rate
        from base t
        join telegram_groups g on g.id = t.group_id
        group by g.id, g.title, g.chat_id
      ) x
  ),
  agents as (
    select coalesce(jsonb_agg(row_to_json(y) order by y.handled_tickets desc), '[]'::jsonb) as payload
      from (
        select
          a.id,
          a.display_name,
          count(*)::int as handled_tickets,
          avg(t.first_response_seconds)::numeric(12,2) as avg_first_response_seconds,
          count(*) filter (where t.status = 'closed')::int as closure_count
        from base t
        join agents a on a.id = t.closed_by_agent_id
        group by a.id, a.display_name
      ) y
  ),
  recent_unresolved as (
    select coalesce(jsonb_agg(row_to_json(z) order by z.created_at desc), '[]'::jsonb) as payload
      from (
        select
          t.id,
          g.title as group_title,
          c.full_name as customer_name,
          c.username as customer_username,
          t.status,
          t.created_at,
          t.last_customer_message_at
        from base t
        join telegram_groups g on g.id = t.group_id
        join customers c on c.id = t.customer_id
        where t.status in ('open', 'reopened', 'auto_replied')
        order by t.created_at desc
        limit 10
      ) z
  )
  select jsonb_build_object(
    'total_requests', count(*)::int,
    'open_requests', count(*) filter (where status in ('open', 'reopened', 'auto_replied'))::int,
    'closed_requests', count(*) filter (where status = 'closed')::int,
    'answered_requests', count(*) filter (where first_response_at is not null or auto_replied_at is not null)::int,
    'unanswered_requests', count(*) filter (where first_response_at is null and auto_replied_at is null)::int,
    'auto_replied_requests', count(*) filter (where auto_replied_at is not null)::int,
    'response_rate',
      coalesce(
        round(
          100.0 * count(*) filter (where first_response_at is not null or auto_replied_at is not null)
          / nullif(count(*), 0),
          2
        ),
        0
      ),
    'average_first_response_seconds', avg(first_response_seconds)::numeric(12,2),
    'median_first_response_seconds', percentile_cont(0.5) within group (order by first_response_seconds),
    'groups', (select payload from groups),
    'agents', (select payload from agents),
    'recent_unresolved', (select payload from recent_unresolved)
  )
  from base;
$$;

create or replace function stats_groups(
  p_from timestamptz,
  p_to timestamptz
)
returns table (
  id uuid,
  title text,
  chat_id bigint,
  total_requests integer,
  open_requests integer,
  closed_requests integer,
  auto_replied_requests integer,
  response_rate numeric,
  average_first_response_seconds numeric
)
language sql
security definer
as $$
  select
    g.id,
    g.title,
    g.chat_id,
    count(*)::int as total_requests,
    count(*) filter (where t.status in ('open', 'reopened', 'auto_replied'))::int as open_requests,
    count(*) filter (where t.status = 'closed')::int as closed_requests,
    count(*) filter (where t.auto_replied_at is not null)::int as auto_replied_requests,
    round(
      100.0 * count(*) filter (where t.first_response_at is not null or t.auto_replied_at is not null)
      / nullif(count(*), 0),
      2
    ) as response_rate,
    avg(t.first_response_seconds)::numeric(12,2) as average_first_response_seconds
  from tickets t
  join telegram_groups g on g.id = t.group_id
  where t.created_at >= p_from
    and t.created_at < p_to
  group by g.id, g.title, g.chat_id
  order by total_requests desc, g.title asc;
$$;

create or replace function stats_agents(
  p_from timestamptz,
  p_to timestamptz
)
returns table (
  id uuid,
  display_name text,
  telegram_username text,
  role text,
  handled_tickets integer,
  avg_first_response_seconds numeric,
  closure_count integer
)
language sql
security definer
as $$
  select
    a.id,
    a.display_name,
    a.telegram_username,
    a.role,
    count(*)::int as handled_tickets,
    avg(t.first_response_seconds)::numeric(12,2) as avg_first_response_seconds,
    count(*) filter (where t.status = 'closed')::int as closure_count
  from tickets t
  join agents a on a.id = t.closed_by_agent_id
  where t.created_at >= p_from
    and t.created_at < p_to
  group by a.id, a.display_name, a.telegram_username, a.role
  order by handled_tickets desc, a.display_name asc;
$$;

create or replace function stats_timeline(
  p_from timestamptz,
  p_to timestamptz,
  p_bucket text default 'day'
)
returns table (
  bucket text,
  total_requests integer,
  closed_requests integer,
  auto_replied_requests integer,
  avg_first_response_seconds numeric
)
language sql
security definer
as $$
  select
    to_char(date_trunc(p_bucket, created_at), 'YYYY-MM-DD HH24:MI:SS') as bucket,
    count(*)::int as total_requests,
    count(*) filter (where status = 'closed')::int as closed_requests,
    count(*) filter (where auto_replied_at is not null)::int as auto_replied_requests,
    avg(first_response_seconds)::numeric(12,2) as avg_first_response_seconds
  from tickets
  where created_at >= p_from
    and created_at < p_to
  group by date_trunc(p_bucket, created_at)
  order by date_trunc(p_bucket, created_at);
$$;

create or replace function management_summary(
  p_from timestamptz,
  p_to timestamptz
)
returns jsonb
language sql
security definer
as $$
  with overview as (
    select stats_overview(p_from, p_to) as payload
  )
  select payload from overview;
$$;
