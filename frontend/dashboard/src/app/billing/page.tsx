import { CreditCard } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";

export default function BillingPage() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Billing"
        description="Manage subscription, usage, invoices, and enterprise agreements."
      />

      <EmptyState
        icon={CreditCard}
        title="Billing is not configured yet"
        description="Billing will be enabled when production usage and pricing plans are connected."
      />
    </div>
  );
}
