"""Provider adapter contracts and registry for verification capabilities.

The built-in AI service is one provider implementation.  Keeping its HTTP
client behind this registry lets tasks remain independent of that transport and
allows a later provider integration to replace one capability at a time.
"""

from collections.abc import Callable
from typing import NotRequired, Protocol, TypedDict

from apps.providers import ai_service


PROVIDER_CONTRACT_VERSION = "1"
SUPPORTED_PROVIDER_STATUSES = {"completed", "failed", "inconclusive"}


class ProviderContractError(ValueError):
    public_message = "Provider returned an invalid contract response."
    error_code = "provider_invalid_response"
    retryable = False


class ProviderResult(TypedDict):
    contract_version: str
    capability: str
    status: str
    error: NotRequired[dict]


def normalize_provider_result(capability: str, result: dict) -> dict:
    if not isinstance(result, dict):
        raise ProviderContractError("Provider operations must return an object result.")
    supplied_version = result.get("contract_version")
    if supplied_version is not None and supplied_version != PROVIDER_CONTRACT_VERSION:
        error = ProviderContractError("Provider contract version is not supported.")
        error.error_code = "provider_contract_version_unsupported"
        raise error
    normalized = dict(result)
    normalized["contract_version"] = PROVIDER_CONTRACT_VERSION
    normalized["capability"] = capability
    normalized.setdefault("status", "completed")
    if (
        not isinstance(normalized["status"], str)
        or normalized["status"] not in SUPPORTED_PROVIDER_STATUSES
    ):
        raise ProviderContractError("Provider response status is not supported.")
    return normalized


class ProviderAdapter(Protocol):
    """The capabilities currently supplied by verification AI providers."""

    def document_quality(self, **kwargs) -> ProviderResult: ...

    def document_classification(self, **kwargs) -> ProviderResult: ...

    def document_ocr(self, **kwargs) -> ProviderResult: ...

    def liveness(self, **kwargs) -> ProviderResult: ...

    def face_compare(self, **kwargs) -> ProviderResult: ...


class BuiltInAIServiceAdapter:
    """Adapter for the platform's internal AI HTTP service."""

    document_quality = staticmethod(ai_service.run_document_quality)
    document_classification = staticmethod(ai_service.run_document_classification)
    document_ocr = staticmethod(ai_service.run_document_ocr)
    liveness = staticmethod(ai_service.run_liveness_check)
    face_compare = staticmethod(ai_service.run_face_compare)


class ProviderAdapterRegistry:
    def __init__(self):
        self._factories: dict[str, Callable[[], ProviderAdapter]] = {}

    def register(self, code: str, factory: Callable[[], ProviderAdapter]) -> None:
        if not code:
            raise ValueError("Provider adapter code cannot be empty.")
        self._factories[code] = factory

    def resolve(self, code: str) -> ProviderAdapter:
        try:
            factory = self._factories[code]
        except KeyError as exc:
            raise LookupError(
                f"No provider adapter is registered for {code!r}."
            ) from exc
        return factory()


BUILT_IN_AI_SERVICE = "built_in_ai_service"
provider_adapter_registry = ProviderAdapterRegistry()
provider_adapter_registry.register(BUILT_IN_AI_SERVICE, BuiltInAIServiceAdapter)


def _built_in_adapter() -> ProviderAdapter:
    return provider_adapter_registry.resolve(BUILT_IN_AI_SERVICE)


# Capability functions preserve the task call sites (and their test seams) while
# ensuring every invocation is resolved through the adapter registry.
def run_document_quality(**kwargs) -> dict:
    return _built_in_adapter().document_quality(**kwargs)


def run_document_classification(**kwargs) -> dict:
    return _built_in_adapter().document_classification(**kwargs)


def run_document_ocr(**kwargs) -> dict:
    return _built_in_adapter().document_ocr(**kwargs)


def run_liveness_check(**kwargs) -> dict:
    return _built_in_adapter().liveness(**kwargs)


def run_face_compare(**kwargs) -> dict:
    return _built_in_adapter().face_compare(**kwargs)
