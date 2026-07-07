import { SessionStatePage } from "@/components/session-state-page";

export default async function VerificationExpiredPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = await params;

  return (
    <SessionStatePage
      title="This verification session has expired"
      description="The secure link is no longer active. Contact the organization that requested your verification so they can send a new session."
      badge={`Session ${sessionId}`}
      icon="expired"
      primaryHref="/"
      primaryLabel="Open another session"
    />
  );
}
