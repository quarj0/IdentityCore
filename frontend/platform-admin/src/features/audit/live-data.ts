import { restRequest } from "@/lib/admin-api";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type AuditEvent = {
  id: string;
  actor_type: string;
  actor_id: string | null;
  action: string;
  action_label: string;
  actor_display_name: string;
  target_type: string;
  target_id: string | null;
  target_label: string;
  ip_address: string | null;
  user_agent: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
};

function formatDate(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function tone(action: string): AdminRecord["statusTone"] {
  if (action.includes("suspend") || action.includes("reject") || action.includes("delete")) {
    return "danger";
  }
  if (action.includes("export") || action.includes("review")) {
    return "info";
  }
  return "success";
}

export function auditEventToRecord(event: AuditEvent): AdminRecord {
  return {
    id: event.id,
    title: event.action_label,
    subtitle: `${event.actor_display_name} · ${event.target_label}${event.target_id ? ` ${event.target_id}` : ""}`,
    status: event.action_label,
    statusTone: tone(event.action),
    primaryMeta: event.target_label,
    secondaryMeta: event.action,
    tertiaryMeta: event.actor_type,
    owner: event.actor_display_name,
    updatedAt: formatDate(event.created_at),
    href: `/audit/${event.id}`,
  };
}

export async function fetchAuditRecords() {
  const data = await restRequest<{ results: AuditEvent[] }>("/platform-admin/audit-events/");
  return data.results.map(auditEventToRecord);
}

export async function fetchAuditRecord(eventId: string) {
  const event = await restRequest<AuditEvent>(`/platform-admin/audit-events/${eventId}`);
  return event;
}

export function buildAuditConfig(records: AdminRecord[]): AdminModuleConfig {
  return {
    moduleLabel: "Platform audit",
    listTitle: "Audit",
    listDescription:
      "Search and inspect platform-wide audit events from the internal ops console.",
    detailBreadcrumbLabel: "Audit",
    searchPlaceholder: "Search audit events...",
    createLabel: "Export",
    exportLabel: "Export audit",
    filters: ["Actor", "Action", "Module"],
    records,
    getRecord: (id) => records.find((record) => record.id === id),
    getMetrics: (record): AdminDetailMetric[] => [
      { label: "Module", value: record.primaryMeta, helper: "audited surface" },
      { label: "Action", value: record.secondaryMeta, helper: "event name" },
      { label: "Actor", value: record.owner, helper: "who triggered it" },
      { label: "Updated", value: record.updatedAt, helper: "event time" },
    ],
    getSections: (record): AdminDetailSection[] => [
      {
        title: "Audit event",
        description: "Immutable record details from the backend audit trail.",
        items: [
          { label: "Event", value: record.title },
          { label: "Description", value: record.subtitle },
          { label: "Actor", value: record.owner },
          { label: "Timestamp", value: record.updatedAt },
        ],
      },
    ],
  };
}
