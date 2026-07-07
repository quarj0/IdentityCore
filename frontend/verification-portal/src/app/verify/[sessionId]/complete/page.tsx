import { SessionStatePage } from "@/components/session-state-page";

export default async function VerificationCompletePage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = await params;

  return (
    <SessionStatePage
      title="Verification submitted"
      description="Your document, selfie, and liveness results were submitted successfully. The requesting organization can now continue its review."
      badge={`Session ${sessionId}`}
      icon="complete"
      primaryHref="/"
      primaryLabel="Return to start"
    />
  );
}
