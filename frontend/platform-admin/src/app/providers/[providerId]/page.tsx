import { VerificationProviderDetailPage } from "@/features/providers/pages/verification-provider-detail-page";

type PageProps = {
  params: {
    providerId: string;
  };
};

export default function Page({ params }: PageProps) {
  return <VerificationProviderDetailPage providerId={params.providerId} />;
}