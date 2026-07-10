import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import { incidentsConfig } from "@/features/incidents/mock-data";

export function IncidentsListPage() {
  return <AdminListPage config={createAdminListConfig(incidentsConfig)} />;
}