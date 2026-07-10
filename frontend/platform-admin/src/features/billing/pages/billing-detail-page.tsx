import { AdminDetailPage } from "@/components/admin-module/admin-detail-page";
import { billingConfig } from "@/features/billing/mock-data";

type BillingDetailPageProps = {
  billingId: string;
};

export function BillingDetailPage({ billingId }: BillingDetailPageProps) {
  return <AdminDetailPage id={billingId} config={billingConfig} />;
}