import importlib.util
import json
from pathlib import Path

from django.test import SimpleTestCase
import yaml

ROOT = Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location(
    "sdk_model_generator", ROOT / "scripts/generate_sdk_models.py"
)
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


class SDKModelGeneratorTests(SimpleTestCase):
    def test_constants_infer_primitives_and_preserve_literals(self):
        for value, kind in (
            (False, "boolean"),
            (True, "boolean"),
            (1, "integer"),
            (1.5, "number"),
            ("draft", "string"),
        ):
            with self.subTest(value=value):
                self.assertEqual(generator.kind({"const": value}), (kind, False))
                self.assertEqual(
                    generator.pytype({"const": value}), f"Literal[{value!r}]"
                )
                self.assertEqual(generator.tstype({"const": value}), json.dumps(value))
        self.assertEqual(generator.cstype({"const": False}), "bool")
        self.assertEqual(generator.jtype({"const": False}), "Boolean")

    def test_fixture_validates_types_enums_constraints_and_nested_values(self):
        schemas = {
            "Fixture": {
                "type": "object",
                "properties": {
                    "expires_at": {"type": "string", "format": "date-time"},
                    "session_token": {"type": "string", "minLength": 1},
                    "decision": {"type": "string", "enum": ["verified", "rejected"]},
                    "subject": {"$ref": "#/components/schemas/Subject"},
                },
                "required": ["expires_at", "session_token", "decision", "subject"],
            },
            "Subject": {
                "type": "object",
                "properties": {"age": {"type": "integer", "minimum": 18}},
                "required": ["age"],
            },
        }
        payload = {
            "expires_at": "2026-08-01T12:30:00Z",
            "session_token": "fixture",
            "decision": "verified",
            "subject": {"age": 18},
        }
        self.assertEqual(generator.validate_fixture(payload, "Fixture", schemas), [])
        for field, value in (
            ("expires_at", 42),
            ("expires_at", "not-a-date"),
            ("session_token", {}),
            ("session_token", ""),
            ("decision", "invalid"),
            ("subject", {"age": "18"}),
            ("subject", {"age": 17}),
        ):
            with self.subTest(field=field, value=value):
                self.assertTrue(
                    generator.validate_fixture(
                        {**payload, field: value}, "Fixture", schemas
                    )
                )

    def test_generates_enum_types_and_omits_only_optional_null_properties(self):
        schemas = {
            "Request": {
                "type": "object",
                "required": ["required_null"],
                "properties": {
                    "purpose": {
                        "type": "string",
                        "enum": ["document_capture", "selfie_capture"],
                    },
                    "optional": {"type": "string"},
                    "required_null": {"type": ["string", "null"]},
                },
            }
        }
        generated = generator.generate(schemas)
        self.assertIn(
            "Literal['document_capture', 'selfie_capture']", generated["python"]
        )
        self.assertIn('"document_capture" | "selfie_capture"', generated["typescript"])
        self.assertIn('DocumentCapture("document_capture")', generated["java"])
        self.assertIn("@JsonValue", generated["java"])
        self.assertIn("RequestPurpose purpose", generated["java"])
        self.assertIn("JsonStringEnumConverter<RequestPurpose>", generated["dotnet"])
        self.assertIn("public RequestPurpose? Purpose", generated["dotnet"])
        self.assertEqual(
            generated["dotnet"].count(
                "JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)"
            ),
            2,
        )
        self.assertNotIn(
            'WhenWritingNull)]\n    [JsonPropertyName("required_null")]',
            generated["dotnet"],
        )

    def test_public_fixture_matches_contract(self):
        schemas = yaml.safe_load(generator.SPEC.read_text())["components"]["schemas"]
        for name, path in generator.FIXTURES.items():
            self.assertEqual(
                generator.validate_fixture(json.loads(path.read_text()), name, schemas),
                [],
            )
