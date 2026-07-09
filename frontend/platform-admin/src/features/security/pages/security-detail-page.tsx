import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import { securityConfig } from "@/features/security/mock-data";

type SecurityDetailPageProps = {
  securityId: string;
};

export function SecurityDetailPage({ securityId }: SecurityDetailPageProps) {
  return <AdminDetailPage id={securityId} config={securityConfig} />;
}