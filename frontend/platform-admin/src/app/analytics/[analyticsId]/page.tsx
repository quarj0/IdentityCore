import { AnalyticsDetailPage } from "@/features/analytics/pages/analytics-detail-page";

type PageProps = { params: { analyticsId: string } };

export default async function Page({ params }: PageProps) {
  const { analyticsId } = await params;
  return <AnalyticsDetailPage analyticsId={analyticsId} />;
}
