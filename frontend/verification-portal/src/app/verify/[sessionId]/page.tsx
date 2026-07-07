import { redirect } from "next/navigation";
import { VerificationSessionFlow } from "@/components/verification-session-flow";
import { fetchVerificationSession } from "@/lib/session-api";

export default async function VerificationSessionPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = await params;
  const session = await fetchVerificationSession(sessionId);

  if (session.status === "expired") {
    redirect(`/verify/${sessionId}/expired`);
  }

  if (session.status === "completed") {
    redirect(`/verify/${sessionId}/complete`);
  }

  if (session.status === "error") {
    redirect(`/verify/${sessionId}/error`);
  }

  return <VerificationSessionFlow initialSession={session} />;
}
