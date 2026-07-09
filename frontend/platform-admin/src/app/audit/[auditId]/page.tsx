import { AuditDetailPage } from "@/features/audit/pages/audit-detail-page";

type PageProps = { params: { auditId: string } };

export default function Page({ params }: PageProps) {
  return <AuditDetailPage auditId={params.auditId} />;
}