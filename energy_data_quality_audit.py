"""Audit a meter CSV for common data-quality problems using only Python's stdlib."""

import argparse
import csv
from datetime import datetime, timedelta
import json
from pathlib import Path
import statistics


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
INPUT_PATH = DATA_DIR / "meter_readings.csv"
EXPECTED_INTERVAL = timedelta(hours=1)


def write_example(path=INPUT_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    start = datetime(2026, 9, 1)
    rows = []
    for hour in range(72):
        if hour == 33:
            continue
        value = 2.2 + (hour % 24) * 0.11 + (hour // 24) * 0.07
        rows.append({
            "timestamp": (start + timedelta(hours=hour)).isoformat(timespec="minutes"),
            "meter_id": "demo-meter-01",
            "energy_kwh": "" if hour == 20 else f"{value:.3f}",
        })
        if hour == 12:
            rows.append(dict(rows[-1]))
        if hour == 51:
            rows[-1]["energy_kwh"] = "999.000"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["timestamp", "meter_id", "energy_kwh"])
        writer.writeheader()
        writer.writerows(rows)


def read_rows(path):
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def audit_rows(rows, expected_interval=EXPECTED_INTERVAL):
    findings = []
    parsed = []
    values = []

    def add(row_number, row, issue, detail):
        findings.append({
            "row_number": row_number,
            "meter_id": row.get("meter_id", ""),
            "timestamp": row.get("timestamp", ""),
            "issue": issue,
            "detail": detail,
        })

    for index, row in enumerate(rows, start=2):
        timestamp_text = (row.get("timestamp") or "").strip()
        meter_id = (row.get("meter_id") or "").strip()
        if not meter_id:
            add(index, row, "missing_meter_id", "meter_id is blank")
        try:
            timestamp = datetime.fromisoformat(timestamp_text)
        except ValueError:
            timestamp = None
            add(index, row, "invalid_timestamp", "timestamp is blank or not ISO-8601")
        energy_text = (row.get("energy_kwh") or "").strip()
        try:
            energy = float(energy_text)
            if energy < 0:
                raise ValueError
            values.append((index, energy))
        except ValueError:
            energy = None
            issue = "missing_energy" if not energy_text else "invalid_energy"
            add(index, row, issue, "energy_kwh must be a non-negative number")
        if timestamp is not None:
            parsed.append((index, timestamp, meter_id, energy))

    seen = set()
    duplicate_count = 0
    grouped = {}
    for index, timestamp, meter_id, energy in parsed:
        key = (meter_id, timestamp)
        if key in seen:
            duplicate_count += 1
            add(index, {"meter_id": meter_id, "timestamp": timestamp.isoformat()},
                "duplicate_timestamp", "same meter_id and timestamp already appeared")
        else:
            seen.add(key)
            grouped.setdefault(meter_id, []).append((index, timestamp))

    irregular_count = 0
    for meter_id, readings in grouped.items():
        readings.sort(key=lambda item: item[1])
        for previous, current in zip(readings, readings[1:]):
            delta = current[1] - previous[1]
            if delta != expected_interval:
                irregular_count += 1
                add(current[0], {"meter_id": meter_id, "timestamp": current[1].isoformat()},
                    "irregular_interval", f"expected {expected_interval}, observed {delta}")

    numeric = [value for _, value in values]
    outlier_count = 0
    if numeric:
        median = statistics.median(numeric)
        mad = statistics.median(abs(value - median) for value in numeric)
        if mad > 0:
            for row_number, value in values:
                modified_z = 0.6745 * abs(value - median) / mad
                if modified_z > 3.5:
                    outlier_count += 1
                    add(row_number, rows[row_number - 2], "robust_outlier",
                        f"modified_z={modified_z:.2f}; review the source reading")

    counts = {}
    for finding in findings:
        counts[finding["issue"]] = counts.get(finding["issue"], 0) + 1
    report = {
        "input_rows": len(rows),
        "rows_with_findings": len({item["row_number"] for item in findings}),
        "finding_counts": counts,
        "duplicate_timestamp_extras": duplicate_count,
        "irregular_intervals": irregular_count,
        "robust_outliers": outlier_count,
        "outlier_method": "modified z-score using median absolute deviation; threshold 3.5",
        "interval_expectation": str(expected_interval),
        "limitations": "Flags are screening signals, not proof of faulty meters or billing errors.",
    }
    return report, findings


def run(input_path=INPUT_PATH):
    if not input_path.exists():
        write_example(input_path)
    rows = read_rows(input_path)
    report, findings = audit_rows(rows)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (RESULTS_DIR / "findings.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["row_number", "meter_id", "timestamp", "issue", "detail"])
        writer.writeheader()
        writer.writerows(findings)
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=INPUT_PATH, help="meter CSV; created with demo data if absent")
    args = parser.parse_args()
    run(args.input)


if __name__ == "__main__":
    main()
