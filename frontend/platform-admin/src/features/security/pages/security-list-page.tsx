import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import { securityConfig } from "@/features/security/mock-data";

export function SecurityListPage() {
  return <AdminListPage config={createAdminListConfig(securityConfig)} />;
}