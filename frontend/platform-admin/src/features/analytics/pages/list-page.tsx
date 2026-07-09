import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { analyticsConfig } from "@/features/analytics/mock-data";

export function AnalyticsListPage() {
  return <AdminListPage config={analyticsConfig} />;
}