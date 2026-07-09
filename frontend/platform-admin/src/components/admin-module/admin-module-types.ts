import type { ReactNode } from "react";

export type AdminRecordStatusTone =
  | "success"
  | "warning"
  | "danger"
  | "neutral"
  | "info";

export type AdminRecord = {
  id: string;
  title: string;
  subtitle: string;
  status: string;
  statusTone: AdminRecordStatusTone;
  primaryMeta: string;
  secondaryMeta: string;
  tertiaryMeta: string;
  owner: string;
  updatedAt: string;
  href: string;
};

export type AdminDetailMetric = {
  label: string;
  value: string;
  helper: string;
};

export type AdminDetailSection = {
  title: string;
  description: string;
  items: {
    label: string;
    value: string;
  }[];
};

export type AdminModuleConfig = {
  moduleLabel: string;
  listTitle: string;
  listDescription: string;
  detailBreadcrumbLabel: string;
  searchPlaceholder: string;
  createLabel: string;
  exportLabel: string;
  filters: string[];
  records: AdminRecord[];
  getRecord: (id: string) => AdminRecord | undefined;
  getMetrics: (record: AdminRecord) => AdminDetailMetric[];
  getSections: (record: AdminRecord) => AdminDetailSection[];
  detailActions?: ReactNode;
};