import { ProtocolError, jsonBytes, digest } from "./wire.js";
export const OPERATION_CONTRACT = "ic-provider-operations-v1";
const FIELDS = [
  "operation_contract",
  "operation_id",
  "configuration_id",
  "tenant_id",
  "project_id",
  "environment",
  "capability",
  "contract_version",
  "request_sha256",
  "lease_generation",
  "deadline",
  "callback_path",
  "lease_token",
];
export function validateBinding(
  binding,
  key,
  { now = new Date(), completion = true } = {},
) {
  if (
    !binding ||
    typeof binding !== "object" ||
    Array.isArray(binding) ||
    Object.keys(binding).sort().join() !== [...FIELDS].sort().join()
  )
    throw new ProtocolError("Operation binding is incomplete.");
  for (const name of FIELDS.filter((name) => name !== "lease_generation"))
    if (typeof binding[name] !== "string")
      throw new ProtocolError("Operation binding field types are invalid.");
  if (
    binding.operation_contract !== OPERATION_CONTRACT ||
    binding.contract_version !== "1" ||
    binding.configuration_id !== key.keyId ||
    binding.tenant_id !== key.tenantId ||
    binding.environment !== key.environment ||
    !key.capabilities.includes(binding.capability) ||
    !Number.isSafeInteger(binding.lease_generation) ||
    binding.lease_generation < 1
  )
    throw new ProtocolError(
      "Operation scope does not match this provider key.",
    );
  for (const name of [
    "operation_id",
    "configuration_id",
    "tenant_id",
    "project_id",
  ])
    if (!/^[A-Za-z0-9_-]{1,64}$/.test(binding[name]))
      throw new ProtocolError("Operation identifiers are invalid.");
  if (
    !/^[0-9a-f]{64}$/.test(binding.request_sha256) ||
    !/^[A-Za-z0-9_-]{16,256}$/.test(binding.lease_token)
  )
    throw new ProtocolError("Operation fingerprint or lease is invalid.");
  if (
    binding.callback_path !==
    `/api/v1/providers/operations/${binding.operation_id}/callback`
  )
    throw new ProtocolError("Operation callback path is invalid.");
  if (
    !/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|[+-]\d\d:\d\d)$/.test(
      binding.deadline,
    )
  )
    throw new ProtocolError("Operation deadline is invalid.");
  const deadline = new Date(binding.deadline);
  const zone = binding.deadline.match(/[+-](\d\d):(\d\d)$/);
  if (
    zone &&
    (Number(zone[2]) > 59 ||
      Number(zone[1]) > 14 ||
      (Number(zone[1]) === 14 && Number(zone[2]) !== 0))
  )
    throw new ProtocolError("Operation deadline is invalid.");
  const parts = binding.deadline.match(
    /^(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)/,
  );
  const [year, month, day, hour, minute, second] = parts.slice(1).map(Number);
  const calendar = new Date(0);
  calendar.setUTCFullYear(year, month - 1, day);
  calendar.setUTCHours(hour, minute, second, 0);
  if (
    year < 1 ||
    calendar.getUTCFullYear() !== year ||
    calendar.getUTCMonth() !== month - 1 ||
    calendar.getUTCDate() !== day ||
    hour > 23 ||
    minute > 59 ||
    second > 59
  )
    throw new ProtocolError("Operation deadline is invalid.");
  if (!Number.isFinite(deadline.getTime()) || (completion && deadline <= now))
    throw new ProtocolError("Operation deadline has expired or is invalid.");
  return deadline;
}
export function validateResult(capability, result) {
  if (
    !result ||
    typeof result !== "object" ||
    Array.isArray(result) ||
    result.contract_version !== "1" ||
    result.capability !== capability ||
    !["completed", "failed", "inconclusive"].includes(result.status)
  )
    throw new ProtocolError("Provider result envelope is invalid.");
  const finite = (value, depth = 0) => {
    if (depth > 64 || (typeof value === "number" && !Number.isFinite(value)))
      throw new ProtocolError("Provider JSON is invalid.");
    if (value && typeof value === "object")
      for (const item of Object.values(value)) finite(item, depth + 1);
  };
  finite(result);
  if (jsonBytes(result).length > 200 * 1024)
    throw new ProtocolError("Provider result exceeds its size limit.");
  if (capability === "liveness" && result.status === "completed") {
    const metrics = result.metrics;
    if (
      !metrics ||
      !Number.isSafeInteger(metrics.face_count) ||
      metrics.face_count < 0 ||
      typeof metrics.avg_detection_confidence !== "number" ||
      !(
        metrics.avg_detection_confidence >= 0 &&
        metrics.avg_detection_confidence <= 1
      )
    )
      throw new ProtocolError("Liveness result metrics are invalid.");
    for (const [name, max] of [
      ["model_name", 120],
      ["model_version", 64],
    ])
      if (
        typeof result[name] !== "string" ||
        !result[name] ||
        result[name].length > max
      )
        throw new ProtocolError("Liveness model provenance is required.");
  }
  return result;
}
export function canonicalBinding(binding) {
  return Object.fromEntries(
    Object.entries(binding).sort(([left], [right]) =>
      left < right ? -1 : left > right ? 1 : 0,
    ),
  );
}
export const bindingDigest = (binding) =>
  digest(jsonBytes(canonicalBinding(binding)));
