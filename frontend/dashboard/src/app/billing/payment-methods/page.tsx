import { CreditCard } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";

export default function Page() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Payment methods"
        description="Manage cards, bank billing, and payment authorization."
      />
      <EmptyState
        icon={CreditCard}
        title="No payment methods"
        description="Payment methods will be available after billing is connected."
      />
    </div>
  );
}
