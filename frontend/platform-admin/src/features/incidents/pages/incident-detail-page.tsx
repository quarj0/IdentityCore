import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import { incidentsConfig } from "@/features/incidents/mock-data";

type IncidentDetailPageProps = {
  incidentId: string;
};

export function IncidentDetailPage({ incidentId }: IncidentDetailPageProps) {
  return <AdminDetailPage id={incidentId} config={incidentsConfig} />;
}