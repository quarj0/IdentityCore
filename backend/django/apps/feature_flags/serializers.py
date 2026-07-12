from apps.feature_flags.models import FeatureFlag


def serialize_feature_flag(flag: FeatureFlag) -> dict:
    return {
        "id": flag.public_id,
        "key": flag.key,
        "title": flag.title,
        "description": flag.description,
        "status": flag.status,
        "rollout_percent": flag.rollout_percent,
        "audience": flag.audience,
        "owner_team": flag.owner_team,
        "channel": flag.channel,
        "metadata": flag.metadata_json,
        "created_by_id": flag.created_by.public_id,
        "created_by_email": flag.created_by.email,
        "created_at": flag.created_at.isoformat(),
        "updated_at": flag.updated_at.isoformat(),
    }
