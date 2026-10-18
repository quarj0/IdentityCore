import { createHash, createHmac } from "node:crypto";
import { isIP } from "node:net";

export const BFF_USER_AGENT = "IdentityCore-Verification-BFF/1";

/** Ingress must overwrite the explicitly trusted header and prevent direct access. */
export function subjectMetadataHeaders(
  request: Request,
  upstreamUrl: string,
  method: string,
  authorization: string,
  id: string,
): Record<string, string> {
  const secret = process.env.VERIFICATION_METADATA_SECRET ?? "";
  if (!secret) {
    if (process.env.NODE_ENV === "production")
      throw new Error("Metadata signing is required.");
    return { "User-Agent": BFF_USER_AGENT };
  }
  if (secret.length < 32)
    throw new Error("Invalid metadata signing configuration.");
  const header = process.env.VERIFICATION_CLIENT_IP_HEADER?.toLowerCase() ?? "";
  if (header && !/^[a-z0-9-]+$/.test(header)) {
    throw new Error("Invalid client IP header configuration.");
  }
  const reported = header ? request.headers.get(header)?.trim() : null;
  const ip =
    reported && !reported.includes("%") && isIP(reported) ? reported : null;
  const userAgent = (request.headers.get("user-agent") ?? "")
    .replace(/[\u0000-\u001f\u007f]/g, "")
    .slice(0, 1024);
  const envelope = Buffer.from(
    JSON.stringify({
      v: 1,
      ts: Math.floor(Date.now() / 1000),
      method,
      path: new URL(upstreamUrl).pathname,
      authorization: createHash("sha256").update(authorization).digest("hex"),
      request_id: id,
      ip,
      user_agent: userAgent,
    }),
  ).toString("base64url");
  return {
    "User-Agent": BFF_USER_AGENT,
    "X-IC-Subject-Metadata": envelope,
    "X-IC-Subject-Signature": createHmac("sha256", secret)
      .update(envelope)
      .digest("hex"),
  };
}
