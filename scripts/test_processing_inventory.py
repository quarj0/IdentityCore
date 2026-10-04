import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "inventory", Path(__file__).with_name("check_processing_inventory.py")
)
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(inventory.INVENTORY.read_text())

    def test_complete_repository_catalog_and_owner_paths_pass(self):
        self.assertEqual(inventory.validate(self.data, inventory.ROOT), [])

    def test_missing_persisted_field_fails(self):
        self.data["field_catalog"].pop()
        self.assertTrue(
            any(
                "undocumented persisted field" in error
                for error in inventory.validate(self.data, inventory.ROOT)
            )
        )

    def test_stale_and_duplicate_field_references_fail(self):
        entry = dict(self.data["field_catalog"][0])
        self.data["field_catalog"].append(entry)
        self.data["field_catalog"].append({**entry, "field": "Missing.private_data"})
        errors = inventory.validate(self.data, inventory.ROOT)
        self.assertTrue(any("duplicate field" in error for error in errors))
        self.assertTrue(any("stale field reference" in error for error in errors))

    def test_owner_and_processing_metadata_are_required(self):
        self.data["activities"][0]["owners"] = ["nonexistent"]
        self.data["activities"][0]["retention"] = ""
        self.data["activities"][0]["locations"] = ["does/not/exist"]
        errors = inventory.validate(self.data, inventory.ROOT)
        self.assertTrue(any("unknown owner" in error for error in errors))
        self.assertTrue(any("missing retention" in error for error in errors))
        self.assertTrue(any("source path does not exist" in error for error in errors))

    def test_encrypted_and_framework_inherited_fields_are_discovered(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "backend/django/apps/example/models.py"
            source.parent.mkdir(parents=True)
            source.write_text(
                "class User(AbstractBaseUser, PermissionsMixin):\n    secret = EncryptedJSONField()\n    contact: str = models.CharField()\n"
            )
            fields = inventory.model_fields(root)
            self.assertEqual(
                {field.split(".")[1] for _, field in fields},
                {
                    "id",
                    "secret",
                    "contact",
                    "password",
                    "last_login",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                },
            )

    def test_nested_abstract_fields_belong_to_each_concrete_model(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "backend/django/apps/example/records.py"
            source.parent.mkdir(parents=True)
            source.write_text(
                "class Timestamp(models.Model):\n    created_at = models.DateTimeField()\n    class Meta:\n        abstract = True\n"
                "class Base(Timestamp):\n    deleted_at = models.DateTimeField()\n    class Meta:\n        abstract = True\n"
                "class Capture(Base):\n    evidence = EncryptedJSONField()\n"
                "class Subject(Base):\n    identity = EncryptedJSONField()\n"
            )
            fields = {field for _, field in inventory.model_fields(root)}
            self.assertEqual(
                fields,
                {
                    "Capture.id",
                    "Capture.created_at",
                    "Capture.deleted_at",
                    "Capture.evidence",
                    "Subject.id",
                    "Subject.created_at",
                    "Subject.deleted_at",
                    "Subject.identity",
                },
            )

    def test_owner_register_cannot_reference_outside_repository(self):
        self.data["owner_register"] = "../outside-register.json"
        self.assertEqual(
            inventory.validate(self.data, inventory.ROOT),
            ["owner register path does not exist"],
        )


if __name__ == "__main__":
    unittest.main()
