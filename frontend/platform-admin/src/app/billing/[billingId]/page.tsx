import { BillingDetailPage } from "@/features/billing/pages/billing-detail-page"; 

type PageProps = { params: { billingId: string } };

export default function Page({ params }: PageProps) {
  return <BillingDetailPage billingId={params.billingId} />;
}