from pathlib import Path


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def guard_except_body(text, header, next_marker, label):
    start = text.find(header)
    if start < 0:
        raise RuntimeError(f"{label}: header not found")
    body_start = start + len(header)
    end = text.find(next_marker, body_start)
    if end < 0:
        raise RuntimeError(f"{label}: end marker not found")
    body = text[body_start:end]
    indented = "".join(("    " + line) if line.strip() else line for line in body.splitlines(True))
    guard = (
        "        with transaction.atomic():\n"
        "            lock_processing_job_for_finalization(processing_job)\n"
    )
    return text[:body_start] + guard + indented + text[end:]


# Validate linked provider evidence against exact stage/capability/resource metadata.
path = Path("backend/django/apps/verifications/processing_jobs.py")
text = path.read_text()
text = replace_once(
    text,
    '''def _provider_check_is_reusable(check) -> bool:\n    from apps.providers.models import ProviderCheckStatus\n\n    return bool(\n        check\n        and check.status == ProviderCheckStatus.COMPLETED\n        and check.normalized_result_json\n    )\n''',
    '''def _provider_check_is_reusable(\n    check, *, check_type: str, metadata_key: str, resource_id: str\n) -> bool:\n    from apps.providers.models import ProviderCheckStatus\n\n    normalized = (check.normalized_result_json or {}) if check else {}\n    metadata = (check.request_metadata_json or {}) if check else {}\n    return bool(\n        check\n        and check.status == ProviderCheckStatus.COMPLETED\n        and normalized\n        and check.check_type == check_type\n        and normalized.get("capability") == check_type\n        and metadata.get(metadata_key) == resource_id\n    )\n''',
    "reusable helper",
)
text = replace_once(
    text,
    '''                if check.normalized_result_json\n                and (check.request_metadata_json or {}).get(metadata_key) == resource_id\n''',
    '''                if _provider_check_is_reusable(\n                    check,\n                    check_type=check_type,\n                    metadata_key=metadata_key,\n                    resource_id=resource_id,\n                )\n''',
    "latest completed validation",
)
text = replace_once(
    text,
    '    liveness_reusable = _provider_check_is_reusable(current)\n',
    '''    liveness_reusable = _provider_check_is_reusable(\n        current,\n        check_type=ProviderCheckType.LIVENESS,\n        metadata_key="liveness_check_id",\n        resource_id=resource.public_id,\n    )\n''',
    "liveness current validation",
)
text = replace_once(
    text,
    '    face_reusable = _provider_check_is_reusable(current)\n',
    '''    face_reusable = _provider_check_is_reusable(\n        current,\n        check_type=ProviderCheckType.FACE_MATCH,\n        metadata_key="face_match_id",\n        resource_id=face_match.public_id,\n    )\n''',
    "face current validation",
)
path.write_text(text)

# Hold exact ownership while provider-route and generic failure evidence is written.
path = Path("backend/django/apps/biometrics/tasks.py")
text = path.read_text()
text = guard_except_body(
    text,
    '    except ProviderRouteExhausted:\n',
    '    except Exception as exc:\n',
    "route exhausted failure guard",
)
text = guard_except_body(
    text,
    '    except Exception as exc:\n',
    '    promote_upload_to_media_by_storage_key(selfie_capture.storage_key)\n',
    "generic failure guard",
)
path.write_text(text)

print("PR #304 review fixes applied")
