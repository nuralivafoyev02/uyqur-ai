export type TicketStatus = "open" | "answered" | "closed" | "reopened" | "auto_replied";

export interface AdminUser {
  id: string;
  username: string;
  display_name: string;
  must_change_password: boolean;
  is_bootstrap: boolean;
}

export interface SessionState {
  authenticated: boolean;
  must_change_password: boolean;
  user: AdminUser | null;
  expires_at?: string;
}

export interface OverviewStats {
  total_requests: number;
  open_requests: number;
  closed_requests: number;
  answered_requests: number;
  unanswered_requests: number;
  auto_replied_requests: number;
  response_rate: number;
  average_first_response_seconds?: number | null;
  median_first_response_seconds?: number | null;
  groups: GroupMetric[];
  agents: AgentMetric[];
  recent_unresolved: RecentTicket[];
}

export interface GroupMetric {
  id: string;
  title: string;
  chat_id: number;
  total_requests: number;
  open_requests: number;
  closed_requests: number;
  auto_replied_requests: number;
  response_rate: number;
}

export interface AgentMetric {
  id: string;
  display_name: string;
  handled_tickets: number;
  avg_first_response_seconds?: number | null;
  closure_count: number;
}

export interface RecentTicket {
  id: string;
  group_title: string;
  customer_name: string;
  customer_username?: string | null;
  status: TicketStatus;
  created_at: string;
  last_customer_message_at: string;
}

export interface GroupItem {
  id: string;
  chat_id: number;
  title: string;
  username?: string | null;
  group_type: "support" | "management";
  is_active: boolean;
  created_at: string;
  updated_at: string;
  metrics?: Partial<GroupMetric>;
}

export interface TicketMessage {
  id: string;
  telegram_message_id: number;
  sender_type: "customer" | "agent" | "bot" | "system";
  username?: string | null;
  full_name: string;
  text_content?: string;
  text?: string;
  created_at: string;
}

export interface TicketItem {
  id: string;
  group_id: string;
  group_title?: string;
  customer_name?: string;
  customer_username?: string | null;
  status: TicketStatus;
  created_at: string;
  updated_at: string;
  first_response_seconds?: number | null;
  auto_reply_confidence?: number | null;
  last_customer_message_at: string;
  closed_by_agent_id?: string | null;
  latest_customer_message_text?: string;
  messages?: TicketMessage[];
}

export interface AgentItem {
  id: string;
  display_name: string;
  telegram_username?: string | null;
  telegram_chat_id?: number | null;
  role: "agent" | "manager" | "admin";
  is_active: boolean;
  handled_tickets?: number;
  avg_first_response_seconds?: number | null;
  closure_count?: number;
}

export interface KBEntry {
  id: string;
  title: string;
  language: string;
  category: string;
  answer_template: string;
  priority: number;
  is_active: boolean;
  confidence_threshold_override?: number | null;
  keywords?: string[];
  synonyms?: string[];
  patterns?: string[];
  kb_terms?: Array<{ term_type: "keyword" | "synonym" | "pattern"; term_value: string }>;
}

export interface SettingsPayload {
  values: Record<string, unknown>;
}

export interface AuditLogItem {
  actor_type: string;
  actor_id?: string | null;
  action: string;
  entity_type?: string | null;
  entity_id?: string | null;
  metadata: Record<string, unknown>;
  created_at?: string;
}
