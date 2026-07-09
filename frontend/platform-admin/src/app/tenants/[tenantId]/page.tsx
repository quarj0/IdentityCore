import { TenantDetailPage } from "@/features/tenants/pages/tenant-detail-page";

type PageProps = {
  params: {
    tenantId: string;
  };
};

export default function Page({ params }: PageProps) {
  return <TenantDetailPage tenantId={params.tenantId} />;
}
