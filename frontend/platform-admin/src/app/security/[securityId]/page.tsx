import { SecurityDetailPage } from "@/features/security/pages/security-detail-page";

type PageProps = { params: { securityId: string } };

export default async function Page({ params }: PageProps) {
  const { securityId } = await params;
  return <SecurityDetailPage securityId={securityId} />;
}
