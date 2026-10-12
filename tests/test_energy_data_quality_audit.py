import unittest

from energy_data_quality_audit import audit_rows


class AuditRowsTests(unittest.TestCase):
    def test_finds_duplicate_gap_missing_value_and_outlier(self):
        rows = [
            {"timestamp": "2026-01-01T00:00", "meter_id": "m1", "energy_kwh": "1.0"},
            {"timestamp": "2026-01-01T01:00", "meter_id": "m1", "energy_kwh": "1.1"},
            {"timestamp": "2026-01-01T01:00", "meter_id": "m1", "energy_kwh": "1.1"},
            {"timestamp": "2026-01-01T03:00", "meter_id": "m1", "energy_kwh": ""},
            {"timestamp": "2026-01-01T04:00", "meter_id": "m1", "energy_kwh": "1.2"},
            {"timestamp": "2026-01-01T05:00", "meter_id": "m1", "energy_kwh": "0.9"},
            {"timestamp": "2026-01-01T06:00", "meter_id": "m1", "energy_kwh": "1.0"},
            {"timestamp": "2026-01-01T07:00", "meter_id": "m1", "energy_kwh": "1.1"},
            {"timestamp": "2026-01-01T08:00", "meter_id": "m1", "energy_kwh": "1.0"},
            {"timestamp": "2026-01-01T09:00", "meter_id": "m1", "energy_kwh": "999"},
        ]
        report, findings = audit_rows(rows)
        issues = {item["issue"] for item in findings}
        self.assertTrue({"duplicate_timestamp", "irregular_interval", "missing_energy", "robust_outlier"} <= issues)
        self.assertEqual(report["duplicate_timestamp_extras"], 1)
        self.assertEqual(report["robust_outliers"], 1)

    def test_bad_timestamp_is_reported_without_crashing(self):
        report, findings = audit_rows([{"timestamp": "bad", "meter_id": "m1", "energy_kwh": "2"}])
        self.assertEqual(report["input_rows"], 1)
        self.assertEqual(findings[0]["issue"], "invalid_timestamp")


if __name__ == "__main__":
    unittest.main()
