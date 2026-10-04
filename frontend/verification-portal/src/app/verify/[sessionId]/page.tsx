import { LiveVerificationFlow } from "@/components/verification/live-verification-flow";

export default async function VerificationSessionPage({
  params,
}: {
  params: Promise<{ sessionId: string }>;
}) {
  const { sessionId } = await params;
  return <LiveVerificationFlow sessionId={sessionId} />;
}
