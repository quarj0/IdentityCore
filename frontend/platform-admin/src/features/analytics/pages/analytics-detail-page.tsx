import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import { analyticsConfig } from "@/features/analytics/mock-data";

type AnalyticsDetailPageProps = {
  analyticsId: string;
};

export function AnalyticsDetailPage({ analyticsId }: AnalyticsDetailPageProps) {
  return <AdminDetailPage id={analyticsId} config={analyticsConfig} />;
}