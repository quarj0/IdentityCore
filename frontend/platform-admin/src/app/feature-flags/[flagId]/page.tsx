import { FeatureFlagDetailPage } from "@/features/feature-flags/pages/future-flags-detail-page"; 

type PageProps = { params: { flagId: string } };

export default function Page({ params }: PageProps) {
  return <FeatureFlagDetailPage flagId={params.flagId} />;
}