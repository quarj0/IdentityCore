export type PendingIdempotentSubmission = {
  fingerprint: string;
  key: string;
};

export function idempotentSubmission(
  payload: unknown,
  pending: PendingIdempotentSubmission | null,
  randomUUID = () => crypto.randomUUID(),
): PendingIdempotentSubmission {
  const fingerprint = JSON.stringify(payload);
  if (pending?.fingerprint === fingerprint) return pending;
  return {
    fingerprint,
    key: `ik_${randomUUID().replaceAll("-", "")}`,
  };
}

export function idempotencyHeaders(key: string): Record<string, string> {
  return { "Idempotency-Key": key };
}
