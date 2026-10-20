/** Verification proxy routing and bounded consumption of raw request bytes. */
export const MAX_PROXY_BODY_BYTES = 26 * 1024 * 1024;
const SAFE_SEGMENT = /^[A-Za-z0-9_-]{1,128}$/;

export function verificationProxyPath(path: string[]): string | null {
  if (!path.length || path.some((segment) => !SAFE_SEGMENT.test(segment)))
    return null;
  let allowed = false;
  if (path[0] === "uploads") {
    allowed =
      path.length === 1 || (path.length === 3 && ["transfer", "complete"].includes(path[2]));
  } else if (path[0] === "sessions" && path[1] && path.length <= 4) {
    if (path.length === 2) allowed = true;
    else if (path[2] === "consent" && path.length === 4)
      allowed = path[3] === "withdraw";
    else if (
      ["status", "consent", "mobile-handoff", "documents", "selfies"].includes(
        path[2],
      )
    )
      allowed = path.length === 3;
    else
      allowed =
        path[2] === "liveness" &&
        (path.length === 3 || path[3] === "challenge");
  }
  if (!allowed) return null;
  return path[0] === "uploads" && path.length === 1
    ? "uploads/"
    : path.join("/");
}

export class ProxyBodyLimitError extends Error {
  constructor() {
    super("Verification request is too large.");
  }
}

export async function readBoundedProxyBody(
  request: Pick<Request, "method" | "body">,
  signal: AbortSignal,
  maxBytes = MAX_PROXY_BODY_BYTES,
): Promise<ArrayBuffer | undefined> {
  if (request.method === "GET" || request.method === "HEAD") return undefined;
  if (!Number.isSafeInteger(maxBytes) || maxBytes < 0)
    throw new RangeError("Invalid proxy body limit");
  const reader = request.body?.getReader();
  if (!reader) return new ArrayBuffer(0);
  // Releasing the reader applies backpressure without destroying the HTTP
  // socket before Next can send an error response. The request lifecycle owns
  // final stream disposal.
  const abort = () => reader.releaseLock();
  signal.addEventListener("abort", abort, { once: true });
  let bytes = new Uint8Array(0);
  let size = 0;
  try {
    if (signal.aborted) throw new DOMException("Request aborted", "AbortError");
    for (;;) {
      let next: ReadableStreamReadResult<Uint8Array>;
      try {
        next = await reader.read();
      } catch (error) {
        if (signal.aborted)
          throw new DOMException("Request aborted", "AbortError");
        throw error;
      }
      if (signal.aborted)
        throw new DOMException("Request aborted", "AbortError");
      if (next.done) break;
      const required = size + next.value.byteLength;
      if (required > maxBytes) throw new ProxyBodyLimitError();
      if (required > bytes.byteLength) {
        const capacity = Math.min(
          maxBytes,
          Math.max(required, bytes.byteLength * 2, 4096),
        );
        const expanded = new Uint8Array(capacity);
        expanded.set(bytes.subarray(0, size));
        bytes = expanded;
      }
      bytes.set(next.value, size);
      size = required;
    }
    return size === bytes.byteLength
      ? bytes.buffer
      : bytes.buffer.slice(0, size);
  } finally {
    signal.removeEventListener("abort", abort);
    reader.releaseLock();
  }
}

export function requestIsSameOrigin(request: Request): boolean {
  if (request.headers.get("sec-fetch-site") === "cross-site") return false;
  const origin = request.headers.get("origin");
  if (!origin) return true;
  try {
    const incoming = new URL(request.url);
    const host = request.headers.get("host");
    if (host) {
      // Next may reconstruct a localhost URL in a standalone server. The
      // browser's Host authority still identifies the requested origin.
      const authority = new URL(`${incoming.protocol}//${host}`);
      if (
        authority.username ||
        authority.password ||
        authority.pathname !== "/" ||
        authority.search ||
        authority.hash
      )
        return false;
      incoming.host = authority.host;
      incoming.port = authority.port;
    }
    const configured = process.env.VERIFICATION_PUBLIC_ORIGIN;
    if (configured) {
      // A fixed deployment origin supports TLS termination without granting
      // arbitrary forwarding headers authority over this CSRF boundary.
      const publicOrigin = new URL(configured);
      if (
        !["https:", "http:"].includes(publicOrigin.protocol) ||
        publicOrigin.username ||
        publicOrigin.password ||
        publicOrigin.pathname !== "/" ||
        publicOrigin.search ||
        publicOrigin.hash ||
        publicOrigin.host !== incoming.host
      )
        return false;
      return origin === publicOrigin.origin;
    }
    return origin === incoming.origin;
  } catch {
    return false;
  }
}

export async function readBoundedRequestText(
  request: Request,
  maxBytes: number,
): Promise<string> {
  if (Number(request.headers.get("content-length") ?? 0) > maxBytes)
    throw new ProxyBodyLimitError();
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10_000);
  try {
    const body = await readBoundedProxyBody(
      request,
      controller.signal,
      maxBytes,
    );
    return new TextDecoder("utf-8", { fatal: true }).decode(body);
  } finally {
    clearTimeout(timeout);
  }
}
