import { SecurityDetailPage } from "@/features/security/pages/security-detail-page";

type PageProps = { params: { securityId: string } };

export default function Page({ params }: PageProps) {
  return <SecurityDetailPage securityId={params.securityId} />;
}