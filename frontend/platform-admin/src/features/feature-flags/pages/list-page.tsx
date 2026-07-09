import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { featureFlagsConfig } from "@/features/feature-flags/mock-data";

export function FeatureFlagsListPage() {
  return <AdminListPage config={featureFlagsConfig} />;
}