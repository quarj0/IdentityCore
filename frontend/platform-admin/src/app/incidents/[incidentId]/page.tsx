import { IncidentDetailPage } from "@/features/incidents/pages/incident-detail-page"; 

type PageProps = { params: { incidentId: string } };

export default function Page({ params }: PageProps) {
  return <IncidentDetailPage incidentId={params.incidentId} />;
}