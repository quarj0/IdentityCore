import { ComplianceDetailPage } from "@/features/compliance/pages/compliance-detail-page";

type PageProps = { params: { policyId: string } };

export default function Page({ params }: PageProps) {
  return <ComplianceDetailPage policyId={params.policyId} />;
}