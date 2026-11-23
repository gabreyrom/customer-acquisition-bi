"""Check frozen source DDL, source integrity, hashes and deterministic regeneration."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import duckdb
from generate_data import FIELDS, sha256

QUERIES = {
    "registration_window": """SELECT count(*) FROM registration
        WHERE registration_at < DATE '2025-01-01' OR registration_at >= DATE '2026-07-01'
           OR recorded_at < registration_at""",
    "touch_clock": """SELECT count(*) FROM marketing_touch t JOIN campaign c USING(campaign_id)
        WHERE t.recorded_at < t.touched_at OR CAST(t.touched_at AS DATE) < c.active_from
           OR CAST(t.touched_at AS DATE) > c.active_through""",
    "feature_clock": """SELECT count(*) FROM registration_feature f JOIN registration r USING(registration_id)
        WHERE f.effective_at <> r.registration_at OR f.recorded_at < f.effective_at""",
    "account_owner": """SELECT count(*) FROM product_account a
        WHERE a.recorded_at < a.opened_at OR NOT EXISTS (
          SELECT 1 FROM identity_link l JOIN registration r ON r.registration_identity=l.identity_key
          WHERE l.identity_key=a.owner_identity AND l.link_state = 'CANDIDATE'
            AND l.canonical_customer_id IS NOT NULL AND r.registration_at < a.opened_at
            AND l.effective_from <= a.opened_at AND l.recorded_at <= a.opened_at
            AND (l.effective_to IS NULL OR a.opened_at < l.effective_to))""",
    "activity_clock_and_amount": """SELECT count(*) FROM product_activity_delivery e JOIN product_account a USING(account_id)
        WHERE e.effective_at < a.opened_at OR e.effective_at >= TIMESTAMPTZ '2026-07-01 00:00:00+00'
           OR e.recorded_at < e.effective_at OR e.amount_cents IS NULL
           OR (e.annual_rate IS NULL) <> (e.balance_kind IS NULL)""",
    "ownership_uniqueness": """SELECT count(*) FROM (
         SELECT a.account_id FROM product_account a LEFT JOIN identity_link l ON l.identity_key=a.owner_identity
         AND l.link_state='CANDIDATE' AND l.effective_from<=a.opened_at AND l.recorded_at<=a.opened_at
         AND (l.effective_to IS NULL OR a.opened_at < l.effective_to)
         GROUP BY a.account_id HAVING count(DISTINCT l.canonical_customer_id) <> 1)""",
    "product_code": """SELECT count(*) FROM product_activity_delivery e JOIN product_account a USING(account_id)
        WHERE NOT CASE a.product
          WHEN 'SAVINGS' THEN e.activity_code IN ('DEP_SETTLED','WITHDRAWAL','SAV_TREASURY_INCOME','SAV_DEPOSIT_INTEREST','SAV_SERVICE','SAV_FEE')
          WHEN 'DEBIT' THEN e.activity_code IN ('PURCHASE_SETTLED','PURCHASE_REFUND','DEBIT_INTERCHANGE','DEBIT_PROCESSING','DEBIT_REWARD','ADJUSTMENT')
          WHEN 'CREDIT' THEN e.activity_code IN ('PURCHASE_SETTLED','CREDIT_INTERCHANGE','CREDIT_PROCESSING','CREDIT_REWARD','CREDIT_INTEREST','CREDIT_FUNDING','CREDIT_LOSS','PRINCIPAL_REPAYMENT','ADJUSTMENT')
          WHEN 'PERSONAL' THEN e.activity_code IN ('LOAN_FUNDING','PRINCIPAL_REPAYMENT','PERSONAL_INTEREST','PERSONAL_FUNDING','PERSONAL_FEE','PERSONAL_SERVICE','ADJUSTMENT')
          WHEN 'MORTGAGE' THEN e.activity_code IN ('LOAN_FUNDING','PRINCIPAL_REPAYMENT','MORTGAGE_INTEREST','MORTGAGE_FUNDING','MORTGAGE_FEE','MORTGAGE_ORIGINATION','ADJUSTMENT')
        END""",
    "accrual_grain": """SELECT count(*) FROM (
        SELECT account_id, CAST(effective_at AS DATE), balance_kind
        FROM product_activity_delivery WHERE balance_kind IS NOT NULL
        GROUP BY ALL HAVING count(*) <> 1)""",
    "conflicting_source_keys": """SELECT count(*) FROM (
        SELECT source_key FROM product_activity_delivery GROUP BY source_key
        HAVING count(DISTINCT hash(account_id, activity_code, effective_at, recorded_at, state,
        amount_cents, annual_rate, balance_kind, original_source_key, adjustment_kind, component)) <> 1)""",
    "reference_integrity": """SELECT count(*) FROM product_activity_delivery e
        WHERE e.original_source_key IS NOT NULL AND NOT EXISTS (
          SELECT 1 FROM product_activity_delivery o WHERE o.source_key=e.original_source_key
          AND o.account_id=e.account_id AND o.effective_at < e.effective_at AND o.recorded_at <= e.recorded_at
          AND ((e.activity_code='PURCHASE_REFUND' AND o.activity_code='PURCHASE_SETTLED') OR
               (e.activity_code='ADJUSTMENT' AND e.component=o.activity_code
                AND e.adjustment_kind IS NOT NULL
                AND (e.adjustment_kind<>'RECOVERY' OR o.activity_code='CREDIT_LOSS'))))""",
    "missing_reference": """SELECT count(*) FROM product_activity_delivery
        WHERE activity_code IN ('ADJUSTMENT','PURCHASE_REFUND') AND original_source_key IS NULL""",
    "cumulative_reduction_cap": """SELECT count(*) FROM (
        SELECT e.original_source_key FROM product_activity_delivery e
        JOIN (SELECT source_key, max(amount_cents) amount_cents FROM product_activity_delivery GROUP BY 1) o
        ON o.source_key=e.original_source_key GROUP BY e.original_source_key
        HAVING sum(e.amount_cents)>max(o.amount_cents))""",
}


def verify(directory, repeated):
    manifest_path = directory / "manifest_v1.0.json"
    draft = manifest_path.read_bytes()
    manifest = json.loads(draft)
    repeat_manifest = json.loads((repeated / manifest_path.name).read_text())
    manifest["data_quality"] = repeat_manifest["data_quality"]
    assert manifest == repeat_manifest, "Generation manifest differs"
    for name, item in manifest["files"].items():
        assert sha256(directory / name) == sha256(repeated / name) == item["sha256"], name
    db = duckdb.connect()
    db.execute("SET TimeZone='UTC'")
    db.execute(Path(__file__).with_name("schema.sql").read_text())
    counts = {}
    for table in FIELDS:
        path = directory / f"{table}.jsonl.gz"
        info = db.execute(f"DESCRIBE {table}").fetchall()
        columns = ", ".join(f"'{col}': '{typ}'" for col, typ, *_ in info)
        projection = ", ".join(col for col, *_ in info)
        db.execute(f"INSERT INTO {table} SELECT {projection} FROM read_json(?, format='newline_delimited', columns={{{columns}}})",
                   [str(path)])
        counts[table] = db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        assert counts[table] == manifest["files"][path.name]["rows"], table
    assert db.execute("SELECT count(*) FROM information_schema.columns WHERE ends_with(column_name,'_cents') AND data_type <> 'BIGINT'").fetchone() == (0,)
    errors = {name: db.execute(sql).fetchone()[0] for name, sql in QUERIES.items()}
    assert not any(errors.values()), errors
    account_counts = dict(db.execute("SELECT product,count(*) FROM product_account GROUP BY 1").fetchall())
    assert account_counts == manifest["product_accounts"]
    resolved = db.execute("""SELECT count(*) FROM (
        SELECT r.registration_id FROM registration r LEFT JOIN identity_link l
          ON l.identity_key=r.registration_identity AND l.recorded_at<=r.registration_at
          AND l.effective_from<=r.registration_at AND (l.effective_to IS NULL OR r.registration_at<l.effective_to)
          AND l.link_state='CANDIDATE'
        GROUP BY 1 HAVING count(DISTINCT l.canonical_customer_id)=1)""").fetchone()[0]
    assert resolved == manifest["canonical_customer_count"]
    exceptions = Counter(row["kind"] for row in json.loads((directory / "expected_source_exceptions.json").read_text()))
    observed = {
        "DUPLICATE_DELIVERY": "SELECT count(*)-count(DISTINCT source_key) FROM product_activity_delivery",
        "AFTER_RECORDED_CUTOFF": "SELECT count(*) FROM product_activity_delivery WHERE recorded_at > TIMESTAMPTZ '2026-07-01 00:00:00+00'",
        "MISSING_PLAN": "SELECT count(*) FROM campaign_day WHERE planned_cents IS NULL",
        "LATE_INTENT": "SELECT count(*) FROM registration_feature WHERE recorded_at > effective_at",
        "LATE_TOUCH": "SELECT count(*) FROM marketing_touch t JOIN registration r USING(visitor_identity) WHERE t.recorded_at > r.registration_at",
    }
    for kind, query in observed.items():
        assert db.execute(query).fetchone()[0] == exceptions[kind], kind
    assert counts["registration"] - resolved == exceptions["IDENTITY_MISSING"] + exceptions["IDENTITY_AMBIGUOUS"]
    monthly = db.execute("""SELECT count(DISTINCT date_trunc('month',registration_at)),
        count(*) FILTER (WHERE registration_at < TIMESTAMPTZ '2025-07-01 00:00:00+00'),
        count(*) FILTER (WHERE registration_at >= TIMESTAMPTZ '2026-06-02 00:00:00+00')
        FROM registration WHERE registration_id NOT LIKE 'RX-%'""").fetchone()
    assert monthly[0] == 18 and min(monthly[1:]) > 0
    activities = dict(db.execute("""SELECT product,count(*) FROM product_activity_delivery
         JOIN product_account USING(account_id) GROUP BY 1 ORDER BY 1""").fetchall())
    variation = dict(db.execute("""SELECT activity_code,count(*) FROM product_activity_delivery
        WHERE activity_code IN ('CREDIT_LOSS','ADJUSTMENT','PURCHASE_REFUND','LOAN_FUNDING','PRINCIPAL_REPAYMENT')
        GROUP BY 1 ORDER BY 1""").fetchall())
    assert min(activities.values()) > 0 and len(variation) == 5
    manifest["data_quality"] = {
        "status": "SOURCE_CHECKS_COMPLETED", "duckdb_version": duckdb.__version__,
        "ddl_source_rows_loaded": counts, "unintended_integrity_failures": errors,
        "intentional_exception_tags": dict(sorted(exceptions.items())),
        "activity_deliveries_by_product": activities, "selected_activity_codes": variation,
        "months_covered": monthly[0], "definitely_mature_365_signups": monthly[1],
        "definitely_immature_30_signups": monthly[2], "deterministic_generation_verified": True,
        "generation_manifest_sha256": hashlib.sha256((repeated / manifest_path.name).read_bytes()).hexdigest(),
        "future_checks": "ELT point-in-time attribution, financial reconciliation, contribution, and forecast comparisons are pending C/D.",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["data_quality"], indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("repeat_directory", type=Path)
    args = parser.parse_args()
    verify(args.directory, args.repeat_directory)
