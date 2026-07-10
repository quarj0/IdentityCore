import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import { complianceConfig } from "@/features/compliance/mock-data";

export function ComplianceListPage() {
  return <AdminListPage config={createAdminListConfig(complianceConfig)} />;
}