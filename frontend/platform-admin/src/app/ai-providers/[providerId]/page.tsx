import { AiProviderDetailPage } from "@/features/ai-providers/pages/ai-provider-detail-page";

type PageProps = {
  params: {
    providerId: string;
  };
};

export default function Page({ params }: PageProps) {
  return <AiProviderDetailPage providerId={params.providerId} />;
}