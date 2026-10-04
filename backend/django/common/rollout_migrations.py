"""Conservative expand-only classification; ambiguous operations fail closed."""

from django.db import migrations, models
from django.contrib.postgres.operations import AddIndexConcurrently


def expand_safe(operation):
    if isinstance(operation, migrations.CreateModel):
        return True
    if isinstance(operation, migrations.AddField):
        # A Python default is removed after migration and cannot protect old-code INSERTs.
        return bool(
            not operation.field.unique
            and not operation.field.primary_key
            and (
                operation.field.null
                or operation.field.db_default is not models.NOT_PROVIDED
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
