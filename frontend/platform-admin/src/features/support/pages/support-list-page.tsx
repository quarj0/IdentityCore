import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import { supportConfig } from "@/features/support/mock-data";

export function SupportListPage() {
  return <AdminListPage config={createAdminListConfig(supportConfig)} />;
}