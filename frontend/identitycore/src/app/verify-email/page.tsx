import { VerifyEmailPanel } from "@/components/verify-email/verify-email-panel";

export default async function VerifyEmailPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string; email?: string }>;
}) {
  const params = await searchParams;

  return (
    <VerifyEmailPanel
      token={params.token}
      emailFromUrl={params.email}
    />
  );
}
