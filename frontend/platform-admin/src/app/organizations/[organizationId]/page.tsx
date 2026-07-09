import { OrganizationDetailPage } from "@/features/organizations/pages/organization-detail-page";

type PageProps = {
  params: {
    organizationId: string;
  };
};

export default function Page({ params }: PageProps) {
  return <OrganizationDetailPage organizationId={params.organizationId} />;
}
