import { FeatureFlagDetailPage } from "@/features/feature-flags/pages/feature-flag-detail-page";

type PageProps = { params: { flagId: string } };

export default function Page({ params }: PageProps) {
  return <FeatureFlagDetailPage flagId={params.flagId} />;
}