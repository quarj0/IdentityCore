import { ApiClientDetailPage } from "@/features/api-clients/pages/api-client-detail-page";

type PageProps = {
  params: {
    clientId: string;
  };
};

export default async function Page({ params }: PageProps) {
  const { clientId } = await params;
  return <ApiClientDetailPage clientId={clientId} />;
}
