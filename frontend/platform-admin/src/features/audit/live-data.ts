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
  actionLabel: string;
  actorDisplayName: string;
  targetType: string;
  targetId: string | null;
  targetLabel: string;
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
  const operationName =
    typeof event.metadata["operation_name"] === "string"
      ? event.metadata["operation_name"]
      : "";
  const label = event.actionLabel || event.action;
  const actor = event.actorDisplayName || event.actorType;
  const moduleLabel = event.targetLabel || event.targetType;
  return {
    id: event.id,
    title: operationName ? `${label} · ${operationName}` : label,
    subtitle: `${actor} · ${moduleLabel}${event.targetId ? ` ${event.targetId}` : ""}`,
    status: label,
    statusTone: tone(`${event.action} ${label}`.toLowerCase()),
    primaryMeta: moduleLabel,
    secondaryMeta: label,
    tertiaryMeta: event.actorType,
    owner: actor,
    updatedAt: formatDateTime(event.createdAt),
    href: `/audit/${event.id}`,
    ipAddress: event.ipAddress,
    userAgent: event.userAgent,
    operationName: operationName || undefined,
    metadata: event.metadata,
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
          actionLabel
          actorDisplayName
          targetType
          targetId
          targetLabel
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
          actionLabel
          actorDisplayName
          targetType
          targetId
          targetLabel
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
      { label: "Action", value: record.secondaryMeta, helper: "human-readable event" },
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
      {
        title: "Request context",
        description: "Request metadata captured when the event was recorded.",
        items: [
          { label: "Operation", value: record.operationName || "Not recorded" },
          { label: "Request IP", value: record.ipAddress || "Not recorded" },
          { label: "User agent", value: record.userAgent || "Not recorded" },
          { label: "Target", value: `${record.primaryMeta}${record.operationName ? ` · ${record.operationName}` : ""}` },
        ],
      },
    ],
  };
}
