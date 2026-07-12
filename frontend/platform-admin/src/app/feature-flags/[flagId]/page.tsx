import { FeatureFlagDetailPage } from "@/features/feature-flags/pages/future-flags-detail-page"; 

type PageProps = { params: { flagId: string } };

export default async function Page({ params }: PageProps) {
  const { flagId } = await params;
  return <FeatureFlagDetailPage flagId={flagId} />;
}
