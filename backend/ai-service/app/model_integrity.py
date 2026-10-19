"""Deployment-pinned model inventory, with streamed hashing and metadata caching."""

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from threading import RLock

_LOCK = RLock()


def file_digest(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fingerprint(path):
    stat = path.lstat()
    return (
        stat.st_dev,
        stat.st_ino,
        stat.st_mode,
        stat.st_size,
        stat.st_mtime_ns,
        stat.st_ctime_ns,
    )


def integrity_errors(settings):
    root = settings.ai_model_root.resolve()
    manifest = settings.model_manifest_path.resolve()
    if not manifest.is_file():
        return [f"models.manifest_missing:{manifest}"]
    expected = settings.ai_model_manifest_sha256.strip().lower()
    if not re.fullmatch(r"[a-f0-9]{64}", expected):
        return ["models.manifest_trust_anchor_required"]
    if settings.insightface_allow_download or settings.paddle_allow_download:
        return ["models.runtime_downloads_forbidden"]
    try:
        # Metadata only on warm calls: changes, additions and removals invalidate
        # the cached streamed digest check. No whole-model allocation per request.
        paths = tuple(sorted(root.rglob("*")))
        snapshot = ((".", _fingerprint(root)),) + tuple(
            (str(p.relative_to(root)), _fingerprint(p))
            for p in paths
            if p.resolve() != manifest
        )
        key = (
            str(root),
            str(manifest),
            _fingerprint(manifest),
            expected,
            settings.insightface_model_name,
            settings.pad_model_relative_path,
            snapshot,
        )
        with _LOCK:
            result = _validate(*key)
        return list(result)
    except (OSError, ValueError):
        return ["models.inventory_unreadable"]


@lru_cache(maxsize=8)
def _validate(
    root_name, manifest_name, manifest_stat, expected, model_name, pad_path, snapshot
):
    root, manifest = Path(root_name), Path(manifest_name)
    if manifest_stat[3] > 2 * 1024 * 1024:
        return ("models.manifest_invalid",)
    if file_digest(manifest) != expected:
        return ("models.manifest_checksum_mismatch",)
    try:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ("models.manifest_invalid",)
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, list) or not files:
        return ("models.manifest_invalid",)
    errors = []
    if payload.get("insightface_model") != model_name:
        errors.append("models.insightface_model_mismatch")
    listed = set()
    for entry in files:
        if not isinstance(entry, dict):
            errors.append("models.manifest_entry_invalid")
            continue
        name, digest = entry.get("path"), entry.get("sha256")
        if (
            not isinstance(name, str)
            or not isinstance(digest, str)
            or not re.fullmatch(r"[a-fA-F0-9]{64}", digest)
            or not name
            or Path(name).is_absolute()
            or Path(name).as_posix() != name
            or ".." in Path(name).parts
            or name in listed
        ):
            errors.append("models.manifest_entry_invalid")
            continue
        listed.add(name)
        path = root / name
        try:
            path.resolve().relative_to(root)
        except ValueError:
            errors.append(f"models.asset_path_invalid:{name}")
            continue
        if path.resolve() == manifest or path.is_symlink():
            errors.append(f"models.asset_path_invalid:{name}")
        elif not path.is_file():
            errors.append(f"models.asset_missing:{name}")
        elif file_digest(path) != digest.lower():
            errors.append(f"models.asset_checksum_mismatch:{name}")
    actual = set()
    for name, _ in snapshot:
        path = root / name
        if path.is_symlink():
            errors.append(f"models.asset_path_invalid:{name}")
        elif path.is_file():
            actual.add(name)
    for name in sorted(actual - listed):
        errors.append(f"models.asset_unlisted:{name}")
    if pad_path not in listed:
        errors.append(f"models.manifest_required_asset_missing:{pad_path}")
    prefix = f"insightface/models/{model_name}/"
    if not any(name.startswith(prefix) and name.endswith(".onnx") for name in listed):
        errors.append("models.manifest_insightface_assets_missing")
    for kind in ("det", "rec"):
        prefix = f"paddleocr/{kind}/"
        if prefix + "inference.yml" not in listed or not any(
            prefix + name in listed
            for name in ("inference.json", "inference.pdmodel", "model.pdmodel")
        ):
            errors.append(f"models.manifest_paddle_assets_missing:{kind}")
    # Reject concurrent mutation while hashing; never cache a mixed inventory as valid.
    for name, before in snapshot:
        if _fingerprint(root / name) != before:
            errors.append("models.inventory_changed")
            break
    if _fingerprint(manifest) != manifest_stat:
        errors.append("models.inventory_changed")
    return tuple(errors)
