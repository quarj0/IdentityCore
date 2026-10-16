import Link from "next/link";
import { CreditCard } from "lucide-react";
import { PageHeading } from "@/components/shared/page-heading";

export default function PaymentMethodsPage() {
  return (
    <main className="space-y-6">
      <PageHeading
        title="Payment methods"
        description="Use secure hosted checkout to pay an issued IdentityCore invoice."
      />
      <section className="rounded-xl border p-6">
        <CreditCard aria-hidden="true" className="mb-3 h-6 w-6" />
        <h2 className="text-lg font-semibold">Secure payment collection</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          IdentityCore does not store card numbers, card security codes, or banking credentials.
          Available payment methods depend on the checkout options supported by the configured payment provider.
          To pay, open an issued invoice and follow its secure payment link.
        </p>
        <Link href="/billing/invoices" className="mt-4 inline-block rounded-md border px-4 py-2 text-sm font-medium">
          View payable invoices
        </Link>
      </section>
    </main>
  );
}
