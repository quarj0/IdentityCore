import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { complianceConfig } from "@/features/compliance/mock-data";

export function ComplianceListPage() {
  return <AdminListPage config={complianceConfig} />;
}