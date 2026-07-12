import { TenantDetailPage } from "@/features/tenants/pages/tenant-detail-page";

type PageProps = {
  params: {
    tenantId: string;
  };
};

export default async function Page({ params }: PageProps) {
  const { tenantId } = await params;
  return <TenantDetailPage tenantId={tenantId} />;
}
