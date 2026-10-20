import {
  createHash,
  createHmac,
  randomBytes,
  timingSafeEqual,
} from "node:crypto";
export const SIGNATURE_VERSION = "ic-provider-v1";
export const MAX_BODY_BYTES = 256 * 1024;
export class ProtocolError extends Error {
  constructor(message) {
    super(message);
    this.name = "ProtocolError";
  }
}
export const digest = (bytes) =>
  createHash("sha256").update(bytes).digest("hex");
export function jsonBytes(value) {
  const sorted = (value) => {
    if (Array.isArray(value)) return value.map(sorted);
    if (value && typeof value === "object")
      return Object.fromEntries(
        Object.entries(value)
          .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
          .map(([key, item]) => [key, sorted(item)]),
      );
    return value;
  };
  return Buffer.from(JSON.stringify(sorted(value)));
}
export function deriveSigningSecret(apiKey) {
  if (typeof apiKey !== "string" || !/^[\x00-\x7f]+$/.test(apiKey))
    throw new ProtocolError("Provider credential is invalid.");
  return createHmac("sha256", apiKey)
    .update("identitycore-provider-hmac-v1")
    .digest("hex");
}
export function canonicalMessage(method, path, timestamp, nonce, body) {
  return Buffer.from(
    [
      SIGNATURE_VERSION,
      method.toUpperCase(),
      path,
      String(timestamp),
      nonce,
      digest(body),
    ].join("\n"),
  );
}
export function sign({
  method,
  path,
  body,
  key,
  timestamp = Math.floor(Date.now() / 1000),
  nonce = randomBytes(24).toString("base64url"),
}) {
  const signature = createHmac("sha256", key.secret)
    .update(canonicalMessage(method, path, timestamp, nonce, body))
    .digest("hex");
  return {
    "X-IC-Key-Id": key.keyId,
    "X-IC-Timestamp": String(timestamp),
    "X-IC-Nonce": nonce,
    "X-IC-Signature-Version": SIGNATURE_VERSION,
    "X-IC-Signature": signature,
  };
}
export async function verify({
  method,
  path,
  body,
  headers,
  keys,
  claimNonce,
  now = Math.floor(Date.now() / 1000),
  maxAgeSeconds = 300,
  expectedNonce,
  replayNamespace = "provider-request",
}) {
  if (
    body.length > MAX_BODY_BYTES ||
    typeof claimNonce !== "function" ||
    !Number.isSafeInteger(maxAgeSeconds) ||
    maxAgeSeconds < 0
  )
    throw new ProtocolError("Provider authentication is unavailable.");
  const normalized = Object.fromEntries(
    Object.entries(headers).map(([name, value]) => [name.toLowerCase(), value]),
  );
  if (Object.keys(normalized).length !== Object.keys(headers).length)
    throw new ProtocolError("Provider authentication failed.");
  const patterns = {
    "x-ic-key-id": /^[A-Za-z0-9_.-]{1,128}$/,
    "x-ic-timestamp": /^[0-9]{1,12}$/,
    "x-ic-nonce": /^[A-Za-z0-9_-]{1,256}$/,
    "x-ic-signature": /^[0-9a-f]{64}$/,
  };
  for (const [name, pattern] of Object.entries(patterns))
    if (typeof normalized[name] !== "string" || !pattern.test(normalized[name]))
      throw new ProtocolError("Provider authentication failed.");
  if (normalized["x-ic-signature-version"] !== SIGNATURE_VERSION)
    throw new ProtocolError("Provider signature version is unsupported.");
  const key = Object.hasOwn(keys, normalized["x-ic-key-id"])
      ? keys[normalized["x-ic-key-id"]]
      : null,
    timestamp = Number(normalized["x-ic-timestamp"]),
    nonce = normalized["x-ic-nonce"];
  if (
    !key ||
    Math.abs(now - timestamp) > maxAgeSeconds ||
    (expectedNonce !== undefined && nonce !== expectedNonce)
  )
    throw new ProtocolError("Provider authentication failed.");
  const expected = sign({ method, path, body, key, timestamp, nonce })[
    "X-IC-Signature"
  ];
  if (
    !timingSafeEqual(
      Buffer.from(expected),
      Buffer.from(normalized["x-ic-signature"]),
    )
  )
    throw new ProtocolError("Provider authentication failed.");
  const replayKey = digest(
    jsonBytes([
      SIGNATURE_VERSION,
      replayNamespace,
      key.tenantId,
      key.environment,
      nonce,
    ]),
  );
  if ((await claimNonce(replayKey, timestamp + maxAgeSeconds + 1)) !== true)
    throw new ProtocolError("Provider nonce was already used.");
  return { key, nonce };
}
// JSON.parse accepts duplicate fields and nonfinite numeric overflow. Walk the
// JSON grammar first so every language accepts the same unambiguous wire input.
export function parseJson(body) {
  if (body.length > MAX_BODY_BYTES)
    throw new ProtocolError("Provider message exceeds its size limit.");
  let input;
  try {
    input = new TextDecoder("utf-8", { fatal: true }).decode(body);
  } catch {
    throw new ProtocolError("Provider JSON is invalid.");
  }
  let index = 0,
    depth = 0;
  const ws = () => {
    while (/[ \t\r\n]/.test(input[index] ?? "x")) index++;
  };
  const string = () => {
    const begin = index++;
    while (index < input.length) {
      const ch = input[index++];
      if (ch === '"') return JSON.parse(input.slice(begin, index));
      if (ch === "\\") index++;
    }
    throw new Error();
  };
  const value = () => {
    ws();
    if (++depth > 64) throw new Error();
    const ch = input[index];
    if (ch === "{") {
      index++;
      ws();
      const names = new Set();
      if (input[index] !== "}")
        while (true) {
          ws();
          if (input[index] !== '"') throw new Error();
          const name = string();
          if (names.has(name)) throw new Error();
          names.add(name);
          ws();
          if (input[index++] !== ":") throw new Error();
          value();
          ws();
          if (input[index] !== ",") break;
          index++;
        }
      if (input[index++] !== "}") throw new Error();
    } else if (ch === "[") {
      index++;
      ws();
      if (input[index] !== "]")
        while (true) {
          value();
          ws();
          if (input[index] !== ",") break;
          index++;
        }
      if (input[index++] !== "]") throw new Error();
    } else if (ch === '"') string();
    else {
      const match =
        /^(?:true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)/.exec(
          input.slice(index),
        );
      if (!match) throw new Error();
      if (
        !["true", "false", "null"].includes(match[0]) &&
        !Number.isFinite(Number(match[0]))
      )
        throw new Error();
      index += match[0].length;
    }
    depth--;
  };
  try {
    value();
    ws();
    if (index !== input.length) throw new Error();
    const parsed = JSON.parse(input);
    if (parsed === null || typeof parsed !== "object" || Array.isArray(parsed))
      throw new Error();
    return parsed;
  } catch {
    throw new ProtocolError("Provider JSON is invalid.");
  }
}
