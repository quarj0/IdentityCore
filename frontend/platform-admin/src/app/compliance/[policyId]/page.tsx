import { ComplianceDetailPage } from "@/features/compliance/pages/compliance-detail-page";

type PageProps = { params: { policyId: string } };

export default async function Page({ params }: PageProps) {
  const { policyId } = await params;
  return <ComplianceDetailPage policyId={policyId} />;
}
