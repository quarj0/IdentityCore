export const REDACTED = "[REDACTED]";
export const REDACTED_BINARY = "[REDACTED_BINARY]";

const MAX_REDACTION_DEPTH = 12;

const SENSITIVE_KEYS = new Set([
  "access_key",
  "access_key_id",
  "secret_key",
  "signature",
  "access_token",
  "address",
  "api_key",
  "authorization",
  "biometric_payload",
  "biometric_template",
  "birth_date",
  "client_ip",
  "client_secret",
  "cookie",
  "credentials",
  "csrf_token",
  "csrfmiddlewaretoken",
  "date_of_birth",
  "device_fingerprint",
  "dob",
  "document_bytes",
  "document_image",
  "document_number",
  "document_storage_key",
  "email",
  "external_reference",
  "face_embedding",
  "face_image",
  "first_name",
  "full_name",
  "ghana_card_number",
  "id_token",
  "image",
  "image_base64",
  "image_bytes",
  "ip",
  "ip_address",
  "last_name",
  "liveness_video",
  "middle_name",
  "mrz",
  "national_id",
  "ocr_text",
  "passport_number",
  "password",
  "passcode",
  "phone",
  "phone_number",
  "postal_address",
  "private_key",
  "raw_document",
  "raw_image",
  "raw_ocr",
  "refresh_token",
  "remote_addr",
  "secret",
  "secret_access_key",
  "selfie",
  "selfie_image",
  "selfie_storage_key",
  "session_token",
  "set_cookie",
  "storage_key",
  "subject_id",
  "tax_identification_number",
  "tin",
  "token",
  "user_agent",
  "verification_subject_id",
]);

const SENSITIVE_SUFFIXES = [
  "_secret_key",
  "_access_key",
  "_access_key_id",
  "_signature",
  "_access_token",
  "_api_key",
  "_authorization",
  "_client_secret",
  "_credential",
  "_credentials",
  "_fingerprint",
  "_password",
  "_private_key",
  "_refresh_token",
  "_secret",
  "_session_token",
  "_storage_key",
  "_subject_id",
  "_token",
  "_user_agent",
];

const SENSITIVE_FRAGMENTS = [
  "biometric",
  "face_embedding",
  "image_base64",
  "image_bytes",
  "liveness_video",
  "selfie_image",
];

function normalizeKey(key: PropertyKey): string {
  return String(key)
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

export function isSensitiveLogKey(key: PropertyKey): boolean {
  const normalized = normalizeKey(key);
  if (!normalized) return false;
  return (
    SENSITIVE_KEYS.has(normalized) ||
    SENSITIVE_SUFFIXES.some((suffix) => normalized.endsWith(suffix)) ||
    SENSITIVE_FRAGMENTS.some((fragment) => normalized.includes(fragment))
  );
}

function isIpv6(value: string): boolean {
  const address = value.split("%")[0];
  if (!address.includes(":")) return false;
  let normalized = address;
  if (address.includes(".")) {
    const lastColon = address.lastIndexOf(":");
    const octets = address.slice(lastColon + 1).split(".");
    if (
      octets.length !== 4 ||
      octets.some((part) => !/^\d{1,3}$/.test(part) || Number(part) > 255)
    )
      return false;
    normalized = address.slice(0, lastColon + 1) + "0:0";
  }
  const parts = normalized.split(":");
  if (parts.some((part) => !/^[0-9a-f]{0,4}$/i.test(part))) return false;
  if (!normalized.includes("::"))
    return parts.length === 8 && parts.every(Boolean);
  if (normalized.indexOf("::") !== normalized.lastIndexOf("::")) return false;
  if (normalized.startsWith(":") && !normalized.startsWith("::")) return false;
  if (normalized.endsWith(":") && !normalized.endsWith("::")) return false;
  return parts.filter(Boolean).length < 8;
}

export function redactLogText(value: string): string {
  const redacted = value
    .replace(/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer [REDACTED]")
    .replace(
      /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b/g,
      REDACTED,
    )
    .replace(/\b(?:AKIA|ASIA)[A-Z0-9]{16}\b/g, REDACTED);
  const assignment = /([\w.-]+)["']?\s*[:=]\s*/g;
  const valuePattern =
    /^(?:\[REDACTED(?:_[A-Z_]+)?\][^,;\n\r&}]*|\[[^\n\r]*|\{[^\n\r]*|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^,;\n\r&}]+)/;
  let output = "";
  let cursor = 0;
  for (const match of redacted.matchAll(assignment)) {
    if (match.index < cursor || !isSensitiveLogKey(match[1])) continue;
    const start = match.index + match[0].length;
    const valueMatch = redacted.slice(start).match(valuePattern);
    if (!valueMatch) continue;
    output += redacted.slice(cursor, match.index) + `${match[1]}=${REDACTED}`;
    cursor = start + valueMatch[0].length;
  }
  return (output + redacted.slice(cursor))
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, REDACTED)
    .replace(/(?<![\w:])[0-9a-f:]*:[0-9a-f:.]*(?:%[\w.-]+)?/gi, (address) =>
      isIpv6(address) ? REDACTED : address,
    )
    .replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, REDACTED)
    .replace(/(?:\+?\d[\d ().-]{7,}\d)/g, REDACTED);
}

export function redactLogValue(
  value: unknown,
  key?: PropertyKey,
  depth = 0,
): unknown {
  if (key !== undefined && isSensitiveLogKey(key)) return REDACTED;
  if (depth >= MAX_REDACTION_DEPTH) return "[REDACTED_DEPTH_LIMIT]";
  if (value === null || value === undefined) return value;
  if (typeof value === "string") return redactLogText(value);
  if (typeof value === "number" || typeof value === "boolean") return value;
  if (ArrayBuffer.isView(value) || value instanceof ArrayBuffer) {
    return REDACTED_BINARY;
  }
  if (Array.isArray(value)) {
    return value.map((item) => redactLogValue(item, undefined, depth + 1));
  }
  if (typeof value === "object") {
    const output: Record<string, unknown> = {};
    for (const [entryKey, entryValue] of Object.entries(value)) {
      output[redactLogText(entryKey)] = redactLogValue(
        entryValue,
        entryKey,
        depth + 1,
      );
    }
    return output;
  }
  return redactLogText(String(value));
}

export type SafeLogLevel = "debug" | "info" | "warn" | "error";

const LOG_METHODS: Record<SafeLogLevel, (payload: unknown) => void> = {
  debug: console.debug.bind(console),
  info: console.info.bind(console),
  warn: console.warn.bind(console),
  error: console.error.bind(console),
};

export function safeLog(
  level: SafeLogLevel,
  event: string,
  context: Record<string, unknown> = {},
): void {
  LOG_METHODS[level]({
    event: redactLogText(event),
    context: redactLogValue(context),
  });
}
