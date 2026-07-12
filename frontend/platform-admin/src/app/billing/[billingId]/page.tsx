import { BillingDetailPage } from "@/features/billing/pages/billing-detail-page"; 

type PageProps = { params: { billingId: string } };

export default async function Page({ params }: PageProps) {
  const { billingId } = await params;
  return <BillingDetailPage billingId={billingId} />;
}
