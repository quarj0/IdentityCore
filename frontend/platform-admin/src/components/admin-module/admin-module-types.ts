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

export type AdminListConfig = Pick<
  AdminModuleConfig,
  | "moduleLabel"
  | "listTitle"
  | "listDescription"
  | "searchPlaceholder"
  | "createLabel"
  | "exportLabel"
  | "filters"
  | "records"
>;

export function createAdminListConfig(
  config: AdminModuleConfig,
): AdminListConfig {
  return {
    moduleLabel: config.moduleLabel,
    listTitle: config.listTitle,
    listDescription: config.listDescription,
    searchPlaceholder: config.searchPlaceholder,
    createLabel: config.createLabel,
    exportLabel: config.exportLabel,
    filters: config.filters,
    records: config.records,
  };
}
