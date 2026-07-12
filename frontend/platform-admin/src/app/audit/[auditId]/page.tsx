import { AuditDetailPage } from "@/features/audit/pages/audit-detail-page";

type PageProps = { params: { auditId: string } };

export default async function Page({ params }: PageProps) {
  const { auditId } = await params;
  return <AuditDetailPage auditId={auditId} />;
}
