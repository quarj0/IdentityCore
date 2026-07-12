import { IncidentDetailPage } from "@/features/incidents/pages/incident-detail-page"; 

type PageProps = { params: { incidentId: string } };

export default async function Page({ params }: PageProps) {
  const { incidentId } = await params;
  return <IncidentDetailPage incidentId={incidentId} />;
}
