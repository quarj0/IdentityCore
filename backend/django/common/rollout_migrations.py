"""Conservative expand-only classification; ambiguous operations fail closed."""

from django.db import migrations
from django.contrib.postgres.operations import AddIndexConcurrently


def expand_safe(operation):
    if isinstance(operation, migrations.CreateModel):
        return True
    if isinstance(operation, migrations.AddField):
        # A Python default is removed after migration and cannot protect old-code INSERTs.
        return bool(
            not operation.field.unique
            and not operation.field.primary_key
            and not operation.field.db_index
            and not operation.field.is_relation
            and (
                operation.field.null
                or (
                    operation.field.db_default is not None
                    and isinstance(operation.field.db_default, (str, int, float, bool))
                )
            )
        )
    if isinstance(
        operation,
        (
            AddIndexConcurrently,
            migrations.AlterModelOptions,
            migrations.AlterModelManagers,
        ),
    ):
        return True
    return False
