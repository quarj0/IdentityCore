import { AdminListPage } from "@/components/admin-module/admin-list-page";
import { createAdminListConfig } from "@/components/admin-module/admin-module-types";
import { billingConfig } from "@/features/billing/mock-data";

export function BillingListPage() {
  return <AdminListPage config={createAdminListConfig(billingConfig)} />;
}