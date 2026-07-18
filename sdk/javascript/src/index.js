import { createHmac, timingSafeEqual } from "node:crypto";
import { randomUUID } from "node:crypto";

export const VERSION = "0.2.0";

export class IdentityCoreError extends Error {
  constructor(message) { super(message); this.name = "IdentityCoreError"; }
}
export class IdentityCoreConnectionError extends IdentityCoreError {
  constructor(message, options) { super(message, options); this.name = "IdentityCoreConnectionError"; }
}
export class IdentityCoreTimeoutError extends IdentityCoreConnectionError {
  constructor(message, options) { super(message, options); this.name = "IdentityCoreTimeoutError"; }
}
export class IdentityCoreAPIError extends IdentityCoreError {
  constructor(message, { code = "request_failed", status = 500, requestId = "", details = {} } = {}) {
    super(message); this.name = "IdentityCoreAPIError"; this.code = code; this.status = status; this.requestId = requestId; this.details = details;
  }
}

function compactQuery(params) {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) if (value !== undefined && value !== null && value !== "") search.set(key, String(value));
  const query = search.toString(); return query ? `?${query}` : "";
}
function subjectToApi(input = {}) {
  return { full_name: input.fullName ?? input.full_name ?? "", email: input.email ?? "", phone_number: input.phoneNumber ?? input.phone_number ?? "", date_of_birth: input.dateOfBirth ?? input.date_of_birth ?? undefined, metadata: input.metadata ?? {} };
}
function delay(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }
function humanMessage(message) {
  const lower = String(message || "").toLowerCase();
  if (["unexpected token", "invalidtag", "not valid json", "json.parse", "syntaxerror"].some((item) => lower.includes(item))) return "The service is temporarily unavailable. Please try again shortly.";
  return message || "Request failed. Please try again.";
}

export function verifyWebhookSignature(payload, { signature, timestamp, signingKey, toleranceSeconds = 300, now = Math.floor(Date.now() / 1000) }) {
  if (!signingKey) throw new IdentityCoreError("signingKey is required.");
  if (toleranceSeconds < 0) throw new IdentityCoreError("toleranceSeconds cannot be negative.");
  const sentAt = Number(timestamp);
  if (!Number.isInteger(sentAt)) throw new IdentityCoreError("Webhook timestamp is invalid.");
  if (Math.abs(Number(now) - sentAt) > toleranceSeconds) return false;
  const raw = Buffer.isBuffer(payload) ? payload : Buffer.from(payload);
  const expected = `sha256=${createHmac("sha256", signingKey).update(`${timestamp}.`).update(raw).digest("hex")}`;
  const received = Buffer.from(String(signature));
  const expectedBytes = Buffer.from(expected);
  return received.length === expectedBytes.length && timingSafeEqual(received, expectedBytes);
}

export class IdentityCoreClient {
  constructor({ apiOrigin, clientId, clientSecret, fetch: fetchImpl = globalThis.fetch, timeout = 30000, maxRetries = 2, retryBackoff = 250, allowBrowser = false }) {
    if (!apiOrigin) throw new IdentityCoreError("apiOrigin is required.");
    try { new URL(apiOrigin); } catch { throw new IdentityCoreError("apiOrigin must be an absolute HTTP(S) URL."); }
    if (!/^https?:/.test(apiOrigin)) throw new IdentityCoreError("apiOrigin must be an absolute HTTP(S) URL.");
    if (!clientId || !clientSecret) throw new IdentityCoreError("clientId and clientSecret are required.");
    if (!fetchImpl) throw new IdentityCoreError("A fetch implementation is required.");
    if (timeout <= 0 || maxRetries < 0 || retryBackoff < 0) throw new IdentityCoreError("timeout must be positive and retry settings cannot be negative.");
    if (!allowBrowser && typeof window !== "undefined") throw new IdentityCoreError("The IdentityCore secret-key SDK is server-side only. Do not expose clientSecret in browser code.");
    this.apiOrigin = apiOrigin.replace(/\/$/, ""); this.clientId = clientId; this.clientSecret = clientSecret; this.fetch = fetchImpl; this.timeout = timeout; this.maxRetries = maxRetries; this.retryBackoff = retryBackoff;
    this.policies = { list: () => this.request("GET", "/policies/"), retrieve: (id) => this.request("GET", `/policies/${id}`) };
    this.verifications = {
      create: (input, options = {}) => this.request("POST", "/verifications/", { purpose: input.purpose, policy_id: input.policyId ?? input.policy_id, project_id: input.projectId ?? input.project_id ?? "", verification_subject: subjectToApi(input.verificationSubject ?? input.verification_subject), external_reference: input.externalReference ?? input.external_reference ?? "", redirect_url: input.redirectUrl ?? input.redirect_url ?? "", metadata: input.metadata ?? {} }, options),
      list: ({ status = "", externalReference = "", page, pageSize } = {}) => this.request("GET", `/verifications/${compactQuery({ status, external_reference: externalReference, page, page_size: pageSize })}`),
      iterate: async function* (options = {}) { let page = 1; do { const result = await this.list({ ...options, page }); for (const item of result.results ?? []) yield item; if (page >= Number(result.pagination?.total_pages ?? page)) return; page += 1; } while (true); },
      retrieve: (id) => this.request("GET", `/verifications/${id}`),
      cancel: (id, { reason = "", idempotencyKey = "" } = {}) => this.request("POST", `/verifications/${id}/cancel`, { reason }, { idempotencyKey }),
      resendLink: (id, { channel = "email", idempotencyKey = "" } = {}) => this.request("POST", `/verifications/${id}/resend-link`, { channel }, { idempotencyKey }),
      evidenceReport: (id) => this.request("GET", `/verifications/${id}/evidence-report`),
    };
  }

  health() { return this.request("GET", "/health"); }

  async request(method, path, body, { idempotencyKey = "", requestId = `req_${randomUUID().replaceAll("-", "")}`, headers: extraHeaders = {} } = {}) {
    method = method.toUpperCase();
    const retryable = ["GET", "HEAD", "OPTIONS"].includes(method) || Boolean(idempotencyKey);
    for (let attempt = 0; attempt <= this.maxRetries; attempt += 1) {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);
      const headers = { Accept: "application/json", "X-Client-Id": this.clientId, Authorization: `Bearer ${this.clientSecret}`, "X-Request-Id": requestId, "User-Agent": `identitycore-node/${VERSION}`, ...extraHeaders };
      const init = { method, headers, signal: controller.signal };
      if (idempotencyKey) headers["Idempotency-Key"] = idempotencyKey;
      if (body !== undefined) { headers["Content-Type"] = "application/json"; init.body = JSON.stringify(body); }
      try {
        const response = await this.fetch(`${this.apiOrigin}/api/v1${path}`, init);
        if (retryable && [408, 429, 500, 502, 503, 504].includes(response.status) && attempt < this.maxRetries) { await delay(this.retryBackoff * (2 ** attempt)); continue; }
        return await this.parse(response);
      } catch (error) {
        if (error instanceof IdentityCoreAPIError) throw error;
        if (retryable && attempt < this.maxRetries) { await delay(this.retryBackoff * (2 ** attempt)); continue; }
        if (error?.name === "AbortError") throw new IdentityCoreTimeoutError("The request timed out. Please try again.", { cause: error });
        throw new IdentityCoreConnectionError("Could not connect to IdentityCore.", { cause: error });
      } finally { clearTimeout(timeoutId); }
    }
    throw new IdentityCoreConnectionError("Could not connect to IdentityCore.");
  }

  async parse(response) {
    const text = await response.text(); let payload;
    try { payload = JSON.parse(text); } catch { throw new IdentityCoreAPIError("The service is temporarily unavailable. Please try again shortly.", { code: "invalid_response", status: response.status }); }
    if (!response.ok || payload.success !== true) { const error = payload.error ?? {}; throw new IdentityCoreAPIError(humanMessage(error.message), { code: error.code ?? "request_failed", status: response.status, requestId: payload.request_id ?? "", details: error.details ?? {} }); }
    return payload.data;
  }
}

