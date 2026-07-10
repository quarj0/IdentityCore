import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import { featureFlagsConfig } from "@/features/feature-flags/mock-data";

type FeatureFlagDetailPageProps = {
  flagId: string;
};

export function FeatureFlagDetailPage({ flagId }: FeatureFlagDetailPageProps) {
  return <AdminDetailPage id={flagId} config={featureFlagsConfig} />;
}