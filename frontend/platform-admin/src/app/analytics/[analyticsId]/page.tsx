import { AnalyticsDetailPage } from "@/features/analytics/pages/analytics-detail-page";

type PageProps = { params: { analyticsId: string } };

export default function Page({ params }: PageProps) {
  return <AnalyticsDetailPage analyticsId={params.analyticsId} />;
}