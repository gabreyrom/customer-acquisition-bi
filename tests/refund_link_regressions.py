"""Compare refund-link regression fixtures against the actual corrected pipeline."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from ingest import BUILD, VALIDATION, rows, run, sha256, write_json


def verify():
    path = VALIDATION / "refund_link_regressions.json"
    fixture = json.loads(path.read_text())
    original = VALIDATION / fixture["source_fixture"]
    source = json.loads(original.read_text())
    ref = json.loads((VALIDATION / "independent_expected.json").read_text())
    assert sha256(original) == ref["fixture_sha256"]
    activity = source["product_activity_delivery"]
    template_id = fixture["refund_template_delivery"]
    template = next(r for r in activity if r["delivery_id"] == template_id)
    purchase_key = fixture["source_purchase"]
    purchase = next(r for r in activity if r["source_key"] == purchase_key)
    assert purchase["amount_cents"] == fixture["source_purchase_cents"]
    results = []
    for case in fixture["cases"]:
        selected = [
            dict(r, **case.get("purchase_overrides", {})) if r["source_key"] == purchase_key else r
            for r in activity if r["delivery_id"] != template_id or case.get("retain_template")
        ]
        selected.extend(dict(template, **overlay) for overlay in case["refunds"])
        scratch = dict(source, product_activity_delivery=selected)
        db, metadata = run(scratch, case["id"], ref["cutoffs"]["effective_exclusive"],
                           ref["cutoffs"]["primary_recorded_inclusive"])
        accepted = rows(db, """SELECT delivery_id,amount_cents FROM accepted_purchase_refund ORDER BY delivery_id""")
        activation = db.execute("""SELECT status,source_key FROM activation WHERE customer_id=? AND product=?""",
                                [fixture["customer_id"], fixture["product"]]).fetchone()
        exceptions = db.execute("""SELECT source_id,reason,json_extract_string(detail,'$.refund_reason')
                         FROM exception_log WHERE source_table='product_activity_delivery' ORDER BY 1,2""").fetchall()
        delivered = {r["delivery_id"] for r in case["refunds"]}
        actual = {
            "accepted_deliveries": [r["delivery_id"] for r in accepted],
            "net_purchase_cents": purchase["amount_cents"] - sum(r["amount_cents"] for r in accepted),
            "purchase_qualifies": activation[1] == purchase_key,
            "activation_status": activation[0],
            "exceptions": [list(r) for r in exceptions if r[0] in delivered],
        }
        results.append({"case": case["id"], "expected": case["expected"], "observed": actual,
                        "status": "PASS" if actual == case["expected"] else "FAIL",
                        "scratch_input_sha256": metadata["source_manifest_sha256"]})
        db.close()
    return {"build": BUILD, "regression_fixture_sha256": sha256(path), "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify()
    write_json(args.output, report)
    failures = sum(r["status"] == "FAIL" for r in report["results"])
    print(f"{len(report['results'])} refund cases, {failures} failures")
    raise SystemExit(bool(failures))
