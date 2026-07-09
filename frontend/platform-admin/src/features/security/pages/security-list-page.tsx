import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { securityConfig } from "@/features/security/mock-data";

export function SecurityListPage() {
  return <AdminListPage config={securityConfig} />;
}