import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import { complianceConfig } from "@/features/compliance/mock-data";

type ComplianceDetailPageProps = {
  policyId: string;
};

export function ComplianceDetailPage({ policyId }: ComplianceDetailPageProps) {
  return <AdminDetailPage id={policyId} config={complianceConfig} />;
}