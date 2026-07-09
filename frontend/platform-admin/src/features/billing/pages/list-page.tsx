import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { billingConfig } from "@/features/billing/mock-data";

export function BillingListPage() {
  return <AdminListPage config={billingConfig} />;
}