import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import { analyticsConfig } from "@/features/analytics/mock-data";

export function AnalyticsListPage() {
  return <AdminListPage config={createAdminListConfig(analyticsConfig)} />;
}