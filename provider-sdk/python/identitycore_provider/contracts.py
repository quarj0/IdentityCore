from datetime import datetime, timezone
from hashlib import sha256
import hmac
import re

from .wire import ProtocolError, json_bytes

OPERATION_CONTRACT = "ic-provider-operations-v1"
BINDING_FIELDS = {
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
}
STATUSES = {"completed", "failed", "inconclusive"}


def validate_result(capability, result):
    if (
        not isinstance(result, dict)
        or result.get("contract_version") != "1"
        or result.get("capability") != capability
        or not isinstance(result.get("status"), str)
        or result.get("status") not in STATUSES
    ):
        raise ProtocolError("Provider result envelope is invalid.")
    if len(json_bytes(result)) > 200 * 1024:
        raise ProtocolError("Provider result exceeds its size limit.")
    if capability == "liveness" and result["status"] == "completed":
        metrics = result.get("metrics")
        if (
            not isinstance(metrics, dict)
            or type(metrics.get("face_count")) is not int
            or metrics["face_count"] < 0
        ):
            raise ProtocolError("Liveness result metrics are invalid.")
        confidence = metrics.get("avg_detection_confidence")
        if type(confidence) not in {int, float} or not 0 <= confidence <= 1:
            raise ProtocolError("Liveness detection confidence is invalid.")
        if any(
            not isinstance(result.get(name), str)
            or not result[name]
            or len(result[name]) > maximum
            for name, maximum in (("model_name", 120), ("model_version", 64))
        ):
            raise ProtocolError("Liveness model provenance is required.")
    return result


def validate_binding(binding, key, *, now=None, completion=True):
    if not isinstance(binding, dict) or set(binding) != BINDING_FIELDS:
        raise ProtocolError("Operation binding is incomplete.")
    if any(
        not isinstance(binding[name], str)
        for name in BINDING_FIELDS - {"lease_generation"}
    ):
        raise ProtocolError("Operation binding field types are invalid.")
    if (
        binding["operation_contract"] != OPERATION_CONTRACT
        or binding["contract_version"] != "1"
        or binding["configuration_id"] != key.key_id
        or binding["tenant_id"] != key.tenant_id
        or binding["environment"] != key.environment
        or binding["capability"] not in key.capabilities
        or type(binding["lease_generation"]) is not int
        or binding["lease_generation"] < 1
        or binding["lease_generation"] > 9007199254740991
    ):
        raise ProtocolError("Operation scope does not match this provider key.")
    for name in ("operation_id", "configuration_id", "tenant_id", "project_id"):
        if (
            not isinstance(binding[name], str)
            or re.fullmatch(r"[A-Za-z0-9_-]{1,64}", binding[name]) is None
        ):
            raise ProtocolError("Operation identifiers are invalid.")
    if (
        not isinstance(binding["request_sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", binding["request_sha256"]) is None
    ):
        raise ProtocolError("Operation fingerprint is invalid.")
    token = binding["lease_token"]
    if (
        not isinstance(token, str)
        or re.fullmatch(r"[A-Za-z0-9_-]{16,256}", token) is None
    ):
        raise ProtocolError("Operation lease is invalid.")
    if (
        binding["callback_path"]
        != f'/api/v1/providers/operations/{binding["operation_id"]}/callback'
    ):
        raise ProtocolError("Operation callback path is invalid.")
    try:
        if (
            re.fullmatch(
                r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-][0-9]{2}:[0-9]{2})",
                binding["deadline"],
            )
            is None
        ):
            raise ValueError()
        zone = re.search(r"[+-]([0-9]{2}):([0-9]{2})$", binding["deadline"])
        if zone and (
            int(zone[2]) > 59
            or int(zone[1]) > 14
            or int(zone[1]) == 14
            and int(zone[2]) != 0
        ):
            raise ValueError()
        deadline = datetime.fromisoformat(binding["deadline"])
        if deadline.tzinfo is None:
            raise ValueError()
    except (ValueError, TypeError):
        raise ProtocolError("Operation deadline is invalid.") from None
    if completion and deadline <= (now or datetime.now(timezone.utc)):
        raise ProtocolError("Operation deadline has expired.")
    return deadline


def same_binding(left, right):
    return hmac.compare_digest(
        sha256(json_bytes(left)).digest(), sha256(json_bytes(right)).digest()
    )
