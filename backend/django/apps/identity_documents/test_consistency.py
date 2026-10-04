from datetime import date
from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.identity_documents.consistency import collect_consistency, validate_rules


class DocumentConsistencyTests(SimpleTestCase):
    def evaluate(
        self,
        *,
        fields=None,
        rules=None,
        issued=None,
        expires=None,
        birth=None,
        mrz=None,
        today=date(2026, 10, 4),
        country="GH"
    ):
        document = SimpleNamespace(
            country_profile_id=country,
            issued_at=issued,
            expires_at=expires,
            extracted_data_json={
                **(fields or {}),
                **({"mrz_evidence": mrz} if mrz else {}),
            },
        )
        subject = SimpleNamespace(date_of_birth=birth, full_name="")
        verification = SimpleNamespace(
            policy_snapshot_json={
                "version": 3,
                "document_consistency_rules": rules or {},
            },
            verification_subject=subject,
        )
        return collect_consistency(document, verification, today=today)

    def test_expiry_boundary_and_country_grace(self):
        self.assertNotIn(
            "document_expired", self.evaluate(expires=date(2026, 10, 4))["issues"]
        )
        self.assertIn(
            "document_expired", self.evaluate(expires=date(2026, 10, 3))["issues"]
        )
        rules = {"version": 1, "countries": {"GH": {"expiry_grace_days": 1}}}
        self.assertNotIn(
            "document_expired",
            self.evaluate(expires=date(2026, 10, 3), rules=rules)["issues"],
        )
        self.assertIn(
            "document_expired",
            self.evaluate(expires=date(2026, 10, 3), rules=rules, country="NG")[
                "issues"
            ],
        )

    def test_signal_does_not_make_an_unconfigured_decision(self):
        result = self.evaluate(expires=date(2020, 1, 1))
        self.assertIn("document_expired", result["issues"])
        self.assertEqual(result["recommended_action"], "ignore")
        result = self.evaluate(
            expires=date(2020, 1, 1),
            rules={
                "version": 1,
                "countries": {"GH": {"actions": {"document_expired": "reject"}}},
            },
        )
        self.assertEqual(result["recommended_action"], "reject")
        self.assertEqual(result["policy_version"], 3)

    def test_age_exact_birthday_and_leap_boundary(self):
        rules = {"version": 1, "countries": {"*": {"minimum_age": 18}}}
        self.assertNotIn(
            "document_age_below_minimum",
            self.evaluate(fields={"date_of_birth": "2008-10-04"}, rules=rules)[
                "issues"
            ],
        )
        self.assertIn(
            "document_age_below_minimum",
            self.evaluate(fields={"date_of_birth": "2008-10-05"}, rules=rules)[
                "issues"
            ],
        )
        self.assertEqual(
            self.evaluate(
                fields={"date_of_birth": "2008-02-29"}, today=date(2026, 2, 28)
            )["age_years"],
            17,
        )
        self.assertEqual(
            self.evaluate(
                fields={"date_of_birth": "2008-02-29"}, today=date(2026, 3, 1)
            )["age_years"],
            18,
        )

    def test_future_issue_invalid_calendar_and_date_order(self):
        self.assertIn(
            "document_issue_date_future",
            self.evaluate(issued=date(2026, 10, 5))["issues"],
        )
        self.assertIn(
            "document_date_invalid",
            self.evaluate(fields={"date_of_birth": "2025-02-29"})["issues"],
        )
        self.assertIn(
            "document_date_order_invalid",
            self.evaluate(issued=date(2020, 1, 2), expires=date(2020, 1, 1))["issues"],
        )

    def test_validity_year_limit_handles_leap_day_without_timedelta_guess(self):
        rules = {"version": 1, "countries": {"*": {"maximum_document_years": 5}}}
        self.assertNotIn(
            "document_validity_too_long",
            self.evaluate(
                issued=date(2020, 2, 29), expires=date(2025, 2, 28), rules=rules
            )["issues"],
        )
        self.assertIn(
            "document_validity_too_long",
            self.evaluate(
                issued=date(2020, 2, 29), expires=date(2025, 3, 1), rules=rules
            )["issues"],
        )

    def test_mrz_century_requires_full_document_evidence(self):
        mrz = {"status": "valid", "fields": {"date_of_birth_mrz": {"value": "100101"}}}
        result = self.evaluate(mrz=mrz)
        self.assertIn("document_birth_date_ambiguous", result["issues"])
        self.assertIsNone(result["age_years"])
        for claimed in (date(1910, 1, 1), date(2010, 1, 1)):
            result = self.evaluate(
                mrz=mrz,
                birth=claimed,
                rules={
                    "version": 1,
                    "countries": {
                        "*": {
                            "minimum_age": 18,
                            "actions": {
                                "document_birth_date_ambiguous": "manual_review"
                            },
                        }
                    },
                },
            )
            self.assertIn("document_birth_date_ambiguous", result["issues"])
            self.assertIsNone(result["age_years"])
            self.assertEqual(result["recommended_action"], "manual_review")
        result = self.evaluate(
            mrz=mrz, birth=date(1910, 1, 1), fields={"date_of_birth": "2010-01-01"}
        )
        self.assertNotIn("document_birth_date_ambiguous", result["issues"])
        self.assertEqual(result["age_years"], 16)
        self.assertIn("document_birth_date_mismatch", result["issues"])

    def test_cross_field_mismatch_and_country_do_not_expose_identity_values(self):
        mrz = {
            "status": "valid",
            "fields": {
                "date_of_birth_mrz": {"value": "740812"},
                "issuing_country": {"value": "NGA"},
                "name": {"value": "EXAMPLE OTHER"},
                "document_number": {"value": "D23145890"},
            },
        }
        result = self.evaluate(
            mrz=mrz,
            birth=date(1974, 8, 13),
            fields={"full_name": "Example Test", "document_number": "OTHER123"},
        )
        self.assertTrue(
            {
                "document_birth_date_mismatch",
                "document_name_mismatch",
                "document_number_mismatch",
                "mrz_country_mismatch",
            }
            <= set(result["issues"])
        )
        self.assertNotIn("D23145890", str(result))
        self.assertNotIn("EXAMPLE", str(result))

    def test_bad_rules_fail_closed_and_country_configuration_is_bounded(self):
        self.assertEqual(
            self.evaluate(rules={"version": 2, "countries": {}})["recommended_action"],
            "manual_review",
        )
        for rules in (
            {"version": 1, "countries": {"GH": {"minimum_age": True}}},
            {"version": 1, "countries": {"ZZ": {}}},
            {"version": 1, "countries": {"GH": {"actions": {"document_expired": {}}}}},
        ):
            with self.assertRaises(ValueError):
                validate_rules(rules)

    def test_malformed_untrusted_mrz_fields_do_not_crash(self):
        self.evaluate(mrz={"status": "valid", "fields": []})
        self.evaluate(
            mrz={"status": "valid", "fields": {"expiry_date_mrz": {"value": {}}}}
        )

    def test_far_future_expiry_with_grace_does_not_overflow(self):
        result = self.evaluate(
            expires=date.max,
            rules={"version": 1, "countries": {"*": {"expiry_grace_days": 365}}},
        )
        self.assertNotIn("document_expired", result["issues"])

    def test_self_reported_birth_date_does_not_establish_document_age(self):
        result = self.evaluate(
            birth=date(2000, 1, 1),
            rules={"version": 1, "countries": {"*": {"minimum_age": 18}}},
        )
        self.assertIsNone(result["age_years"])
        self.assertIn("document_birth_date_unavailable", result["issues"])

    def test_utc_midnight_changes_expiry_signal(self):
        from datetime import datetime, timezone as utc
        from unittest.mock import patch

        document = SimpleNamespace(
            country_profile_id="GH",
            issued_at=None,
            expires_at=date(2026, 10, 4),
            extracted_data_json={},
        )
        verification = SimpleNamespace(
            policy_snapshot_json={},
            verification_subject=SimpleNamespace(date_of_birth=None, full_name=""),
        )
        with patch(
            "apps.identity_documents.consistency.timezone.now",
            return_value=datetime(2026, 10, 4, 23, 59, 59, tzinfo=utc.utc),
        ):
            self.assertNotIn(
                "document_expired",
                collect_consistency(document, verification)["issues"],
            )
        with patch(
            "apps.identity_documents.consistency.timezone.now",
            return_value=datetime(2026, 10, 5, 0, 0, 0, tzinfo=utc.utc),
        ):
            self.assertIn(
                "document_expired",
                collect_consistency(document, verification)["issues"],
            )

    def test_claimed_future_date_is_not_document_future_evidence(self):
        result = self.evaluate(
            birth=date(2030, 1, 1),
            rules={
                "version": 1,
                "countries": {
                    "*": {"actions": {"document_birth_date_future": "reject"}}
                },
            },
        )
        self.assertNotIn("document_birth_date_future", result["issues"])
        self.assertEqual(result["recommended_action"], "ignore")
