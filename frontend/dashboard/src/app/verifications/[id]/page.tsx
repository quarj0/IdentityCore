import { VerificationDetailPage } from "@/features/verifications/pages/verification-detail-page";

export default function Page({ params }: { params: { id: string } }) {
  return <VerificationDetailPage id={params.id} />;
}
