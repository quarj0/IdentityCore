"""Frozen legacy publication-name recovery for migrations 0004/0006.

Published policies were immutable and retained the original name even when their
parent workflow was later renamed. Never substitute the mutable parent name.
"""


def recovered_name(version):
    policy = version.policy
    workflow = version.workflow
    if (
        policy.tenant_id != workflow.tenant_id
        or policy.project_id != workflow.project_id
    ):
        return ""
    name = policy.name
    unique_suffix = f" [{workflow.public_id}] workflow policy"
    if name.endswith(unique_suffix):
        name = name[: -len(unique_suffix)]
        # The newer publisher truncates at 180 characters. Exact recovery cannot
        # distinguish an originally longer name from an exactly-180-character one.
        return name if 0 < len(name) < 180 else ""
    if version.published_by.is_platform_admin:
        suffix = " workflow policy"
        if not name.endswith(suffix):
            return ""
        name = name[: -len(suffix)]
    return name if isinstance(name, str) and 0 < len(name) <= 255 else ""
