import { VerificationProviderDetailPage } from "@/features/providers/pages/verification-provider-detail-page";

type PageProps = {
  params: {
    providerId: string;
  };
};

export default async function Page({ params }: PageProps) {
  const { providerId } = await params;
  return <VerificationProviderDetailPage providerId={providerId} />;
}
