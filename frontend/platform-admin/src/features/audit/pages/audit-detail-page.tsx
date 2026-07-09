import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import { auditConfig } from "@/features/audit/mock-data";

type AuditDetailPageProps = {
  auditId: string;
};

export function AuditDetailPage({ auditId }: AuditDetailPageProps) {
  return <AdminDetailPage id={auditId} config={auditConfig} />;
}