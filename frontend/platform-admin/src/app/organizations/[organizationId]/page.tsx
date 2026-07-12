import { OrganizationDetailPage } from "@/features/organizations/pages/organization-detail-page";

type PageProps = {
  params: {
    organizationId: string;
  };
};

export default async function Page({ params }: PageProps) {
  const { organizationId } = await params;
  return <OrganizationDetailPage organizationId={organizationId} />;
}
