import { redirect } from "next/navigation";

export default async function PaymentReturnPage({
  searchParams,
}: {
  searchParams: Promise<{ payment_id?: string | string[] }>;
}) {
  const value = (await searchParams).payment_id;
  const paymentId =
    typeof value === "string" && /^bpa_[A-Za-z0-9]{1,64}$/.test(value)
      ? value
      : "";
  redirect(
    paymentId
      ? `/billing/invoices?payment_id=${encodeURIComponent(paymentId)}`
      : "/billing/invoices",
  );
}
