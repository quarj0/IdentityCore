import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import { featureFlagsConfig } from "@/features/feature-flags/mock-data";

export function FeatureFlagsListPage() {
  return <AdminListPage config={createAdminListConfig(featureFlagsConfig)} />;
}