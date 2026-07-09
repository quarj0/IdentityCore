import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { auditConfig } from "@/features/audit/mock-data";

export function AuditListPage() {
  return <AdminListPage config={auditConfig} />;
}