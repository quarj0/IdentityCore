import { FileText } from "lucide-react";
import { EmptyState } from "@/components/shared/empty-state";
import { PageHeading } from "@/components/shared/page-heading";

export default function Page() {
  return (
    <div className="space-y-8">
      <PageHeading
        title="Invoices"
        description="View billing invoices and receipts."
      />
      <EmptyState
        icon={FileText}
        title="No invoices yet"
        description="Invoices will appear after billing is enabled."
      />
    </div>
  );
}
