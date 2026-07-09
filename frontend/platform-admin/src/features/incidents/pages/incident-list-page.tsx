import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { incidentsConfig } from "@/features/incidents/mock-data";

export function IncidentsListPage() {
  return <AdminListPage config={incidentsConfig} />;
}