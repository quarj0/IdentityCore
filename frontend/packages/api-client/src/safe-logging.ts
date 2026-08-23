export const REDACTED = "[REDACTED]";
export const REDACTED_BINARY = "[REDACTED_BINARY]";

const MAX_REDACTION_DEPTH = 12;

const SENSITIVE_KEYS = new Set([
  "access_key",
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

export function redactLogText(value: string): string {
  return value
    .replace(/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer [REDACTED]")
    .replace(
      /\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b/g,
      REDACTED,
    )
    .replace(/\b(?:AKIA|ASIA)[A-Z0-9]{16}\b/g, REDACTED)
    .replace(
      /\b(authorization|password|passcode|secret|token|api[_-]?key|client[_-]?secret|access[_-]?key|refresh[_-]?token|session[_-]?token|cookie|email|phone(?:_number)?|first[_-]?name|last[_-]?name|full[_-]?name|address|document[_-]?number|passport[_-]?number|national[_-]?id|date[_-]?of[_-]?birth|dob|external[_-]?reference|device[_-]?fingerprint|subject[_-]?id|verification[_-]?subject[_-]?id|client[_-]?ip|ip[_-]?address|remote[_-]?addr|user[_-]?agent|selfie(?:_image)?|image[_-]?base64|ocr[_-]?text|mrz|biometric[_-]?(?:payload|template))\b\s*[:=]\s*(["']?)([^,;\n\r"'}]+)\2/gi,
      (_match, label: string) => `${label}=${REDACTED}`,
    )
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, REDACTED)
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
  if (value instanceof Uint8Array || value instanceof ArrayBuffer) {
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
