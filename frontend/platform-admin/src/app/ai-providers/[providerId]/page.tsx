import { AiProviderDetailPage } from "@/features/ai-providers/pages/ai-provider-detail-page";

type PageProps = {
  params: {
    providerId: string;
  };
};

export default async function Page({ params }: PageProps) {
  const { providerId } = await params;
  return <AiProviderDetailPage providerId={providerId} />;
}
