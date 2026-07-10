import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import { auditConfig } from "@/features/audit/mock-data";

export function AuditListPage() {
  return <AdminListPage config={createAdminListConfig(auditConfig)} />;
}