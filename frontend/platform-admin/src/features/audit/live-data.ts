"use client";

import { graphqlRequest } from "@/lib/admin-api";
import { formatDateTime } from "@/lib/admin-format";
import type {
  AdminDetailMetric,
  AdminDetailSection,
  AdminModuleConfig,
  AdminRecord,
} from "@/components/admin-module/admin-module-types";

type AuditEvent = {
  id: string;
  actorType: string;
  actorId: string | null;
  action: string;
  targetType: string;
  targetId: string | null;
  ipAddress: string | null;
  userAgent: string | null;
  metadata: Record<string, unknown>;
  createdAt: string;
};

type AuditResponse = {
  platformAuditEvents: AuditEvent[];
  platformAuditEvent: AuditEvent | null;
};

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
    title: event.action,
    subtitle: `${event.actorType} · ${event.targetType}${event.targetId ? ` ${event.targetId}` : ""}`,
    status: event.action,
    statusTone: tone(event.action.toLowerCase()),
    primaryMeta: event.targetType,
    secondaryMeta: event.action,
    tertiaryMeta: event.actorType,
    owner: event.actorId ?? "system",
    updatedAt: formatDateTime(event.createdAt),
    href: `/audit/${event.id}`,
  };
}

export async function fetchAuditRecords() {
  const data = await graphqlRequest<AuditResponse>(
    `
      query PlatformAuditEvents($page: Int!, $pageSize: Int!) {
        platformAuditEvents(page: $page, pageSize: $pageSize) {
          id
          actorType
          actorId
          action
          targetType
          targetId
          ipAddress
          userAgent
          metadata
          createdAt
        }
      }
    `,
    { page: 1, pageSize: 100 },
  );
  return data.platformAuditEvents.map(auditEventToRecord);
}

export async function fetchAuditRecord(eventId: string) {
  const data = await graphqlRequest<AuditResponse>(
    `
      query PlatformAuditEvent($eventId: String!) {
        platformAuditEvent(auditId: $eventId) {
          id
          actorType
          actorId
          action
          targetType
          targetId
          ipAddress
          userAgent
          metadata
          createdAt
        }
      }
    `,
    { eventId },
  );
  return data.platformAuditEvent;
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
