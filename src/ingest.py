"""Run the frozen DuckDB ELT on controlled evidence and the verified source extract."""

import argparse
from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import duckdb
from calculate_ltv import score
from generate_data import FIELDS, sha256

ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "data/validation_cases"
SOURCES = ROOT / "data/synthetic_sources"
BUILD = "C-1.0.1"


def exact_ratio(numerator, denominator, scale):
    if numerator is None or not denominator:
        return None
    quotient, remainder = divmod(abs(numerator) * 10**scale, abs(denominator))
    value = quotient + (2 * remainder >= abs(denominator))
    return Decimal(-value if (numerator < 0) != (denominator < 0) else value).scaleb(-scale)


def setup(sources, case, effective, recorded):
    db = duckdb.connect(config={"threads": 4})
    db.execute("SET TimeZone='UTC'")
    db.create_function("exact_ratio", exact_ratio, ["HUGEINT", "HUGEINT", "INTEGER"],
                       "DECIMAL(28,8)", null_handling="special")
    db.execute((ROOT / "src/schema.sql").read_text())
    metadata = {}
    if isinstance(sources, dict):
        fixture_path = VALIDATION / "controlled_source.json"
        if sources == json.loads(fixture_path.read_text()):
            source_digest = sha256(fixture_path)
        else:
            source_digest = hashlib.sha256(json.dumps(sources, sort_keys=True).encode()).hexdigest()
    else:
        manifest_path = sources / "manifest_v1.0.json"
        source_digest = sha256(manifest_path)
        metadata = json.loads(manifest_path.read_text())["files"]
        for table in FIELDS:
            name = f"{table}.jsonl.gz"
            if sha256(sources / name) != metadata[name]["sha256"]:
                raise ValueError(f"Source hash mismatch: {name}")
    counts = {}
    for table in FIELDS:
        columns = db.execute(f"DESCRIBE {table}").fetchall()
        names = [row[0] for row in columns]
        if isinstance(sources, dict):
            rows = [[source[column] for column in names] for source in sources[table]]
            db.executemany(f"INSERT INTO {table} VALUES ({','.join('?' for _ in names)})", rows)
            counts[table] = len(rows)
        else:
            types = ", ".join(f"'{row[0]}': '{row[1]}'" for row in columns)
            db.execute(f"INSERT INTO {table} SELECT {','.join(names)} FROM read_json(?,"
                       f"format='newline_delimited', columns={{{types}}})",
                       [str(sources / f"{table}.jsonl.gz")])
            counts[table] = db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
            if counts[table] != metadata[f"{table}.jsonl.gz"]["rows"]:
                raise ValueError(f"Source row count mismatch: {table}")
    db.execute("INSERT INTO run_manifest VALUES (?,?,?,?,?,?)",
               [case, effective, recorded, source_digest, "1.0", BUILD])
    return db, {"run_id": case, "effective_cutoff": effective, "recorded_cutoff": recorded,
                "source_manifest_sha256": source_digest, "source_row_counts": counts,
                "source_files": metadata}


def adjustments(db):
    rows = db.execute("""
      SELECT a.run_id,a.delivery_id,a.source_key,a.account_id,a.customer_id,a.component,a.amount_cents,
        a.adjustment_kind,a.effective_at,a.recorded_at,a.state,
        f.event_id,f.signed_cents,f.event_code,f.class,f.effective_at,f.recorded_at
      FROM activity a LEFT JOIN financial_event f ON f.run_id=a.run_id
       AND f.source_key=a.original_source_key AND f.event_code=a.component
       AND f.account_id=a.account_id AND f.customer_id=a.customer_id
      WHERE a.activity_code='ADJUSTMENT' AND a.status='ACCEPTED'
      ORDER BY a.effective_at,a.recorded_at,a.source_key
    """).fetchall()
    reductions = defaultdict(int)
    valid, invalid = [], []
    for row in rows:
        run, delivery, key, account, customer, component, amount, kind, effective, recorded, state = row[:11]
        original, original_amount, code, cls, original_effective, original_recorded = row[11:]
        reason = None
        if (original is None or amount is None or kind is None or recorded < original_recorded
                or effective < original_effective or state not in ("POSTED", "CONFIRMED", "SETTLED")
                or (kind == "RECOVERY" and (state != "CONFIRMED" or not code.endswith("_LOSS")))):
            reason = "INVALID_ADJUSTMENT"
        elif amount + reductions[original] > original_amount:
            reason = "OVER_REVERSAL"
        if reason:
            invalid.append((run, delivery, reason, json.dumps({"source_key": key})))
            continue
        reductions[original] += amount
        event = f"{key}/{component}"
        valid.append((run, event, key, component, account, customer, code, cls, -amount,
                      original_effective if kind == "RESTATEMENT_REDUCTION" else effective,
                      recorded, original, kind))
    if valid:
        cols = [row[0] for row in db.execute("DESCRIBE financial_event").fetchall()]
        db.execute("INSERT INTO financial_event SELECT unnest($1, recursive := true)",
                   [[dict(zip(cols, row)) for row in valid]])
    if invalid:
        db.executemany("""INSERT INTO exception_log
            SELECT ?,'product_activity_delivery',?,?,recorded_cutoff,? FROM run_manifest""", invalid)


def validate_operational_refunds(db):
    """Use only valid, capped refund links to reduce qualifying purchases."""
    db.execute("""CREATE TEMP TABLE accepted_purchase_refund (
                    delivery_id VARCHAR PRIMARY KEY, original_source_key VARCHAR NOT NULL,
                    amount_cents BIGINT NOT NULL)""")
    candidates = db.execute("""
        SELECT r.delivery_id,r.source_key,r.original_source_key,r.account_id,r.customer_id,
               r.amount_cents,r.state,r.effective_at,r.recorded_at,
               o.account_id,o.customer_id,o.activity_code,o.state,o.effective_at,o.recorded_at,o.amount_cents
        FROM activity r LEFT JOIN activity o ON o.run_id=r.run_id AND o.source_key=r.original_source_key
          AND o.status='ACCEPTED'
        WHERE r.activity_code='PURCHASE_REFUND' AND r.status='ACCEPTED'
        ORDER BY r.effective_at,r.recorded_at,r.source_key,r.delivery_id
    """).fetchall()
    reductions = defaultdict(int)
    accepted, rejected = [], []
    for row in candidates:
        delivery, key, parent, account, customer, amount, state, effective, recorded = row[:9]
        original_account, owner, code, original_state, original_effective, original_recorded, cap = row[9:]
        error = None
        if original_account is None or code != "PURCHASE_SETTLED":
            error = ("INVALID_REFERENCE", "MISSING_OR_NON_PURCHASE_ORIGINAL")
        elif (account, customer) != (original_account, owner):
            error = ("INVALID_REFERENCE", "ACCOUNT_OR_CUSTOMER_MISMATCH")
        elif state != "SETTLED" or original_state != "SETTLED":
            error = ("INVALID_STATE", "REFUND_OR_PURCHASE_NOT_SETTLED")
        elif effective <= original_effective or recorded < original_recorded:
            error = ("INVALID_REFERENCE", "REFUND_CHRONOLOGY")
        elif amount is None or amount <= 0 or cap is None or cap <= 0:
            error = ("INVALID_ADJUSTMENT", "NONPOSITIVE_OR_MISSING_AMOUNT")
        elif reductions[parent] + amount > cap:
            error = ("OVER_REVERSAL", "CUMULATIVE_REFUND_EXCEEDS_PURCHASE")
        if error:
            reason, detail = error
            rejected.append((delivery, reason, json.dumps({
                "source_key": key, "original_source_key": parent, "refund_reason": detail,
            })))
        else:
            reductions[parent] += amount
            accepted.append((delivery, parent, amount))
    if accepted:
        db.executemany("INSERT INTO accepted_purchase_refund VALUES (?,?,?)", accepted)
    if rejected:
        db.executemany("""INSERT INTO exception_log
            SELECT run_id,'product_activity_delivery',?,?,recorded_cutoff,? FROM run_manifest""", rejected)


def run(sources, case, effective, recorded):
    db, metadata = setup(sources, case, effective, recorded)
    sql = ROOT / "src/transformations"
    for step in ("01_identity_spend.sql", "02_financial.sql"):
        db.execute((sql / step).read_text())
    adjustments(db)
    validate_operational_refunds(db)
    score(db)
    db.execute((sql / "03_reporting.sql").read_text())
    return db, metadata


def rows(db, query):
    cursor = db.execute(query)
    fields = [col[0] for col in cursor.description]
    return [dict(zip(fields, row)) for row in cursor.fetchall()]


def json_value(value):
    if isinstance(value, datetime):
        return value.isoformat().replace("+00:00", "Z")
    if isinstance(value, (Decimal, date)):
        return str(value)
    raise TypeError(type(value).__name__)


def write_json(path, value):
    path.write_text(json.dumps(value, default=json_value, indent=2) + "\n")


TOTALS = """coalesce(sum(signed_cents) FILTER(WHERE class='REVENUE'),0)::BIGINT revenue_cents,
            coalesce(sum(signed_cents) FILTER(WHERE class='COST'),0)::BIGINT cost_cents,
            revenue_cents-cost_cents contribution_cents"""
LEDGER_JOIN = """FROM financial_event f JOIN canonical_activity c USING(run_id,source_key)
                 JOIN product_activity_delivery d USING(delivery_id)
                 LEFT JOIN financial_event o ON o.run_id=f.run_id AND o.event_id=f.original_event_id"""


def controlled(output):
    ref = json.loads((VALIDATION / "independent_expected.json").read_text())
    source_path = VALIDATION / "controlled_source.json"
    if sha256(source_path) != ref["fixture_sha256"]:
        raise ValueError("Controlled input SHA-256 does not match D's reference")
    src = json.loads(source_path.read_text())
    cut = ref["cutoffs"]
    observed, run_notes = [], []
    ledger_query = """SELECT d.delivery_id,f.source_key,f.account_id,f.customer_id,f.event_code,
                       f.class event_class,f.signed_cents,f.effective_at,f.recorded_at,
                       o.source_key original_source_key """ + LEDGER_JOIN

    def compare(group, expected, got, keys, snapshot):
        indexed = {tuple(r[k] for k in keys): r for r in got}
        expected_keys = set()
        for row in expected:
            key = tuple(row[k] for k in keys)
            expected_keys.add(key)
            actual = indexed.get(key)
            selected = None if actual is None else {k: actual.get(k) for k in row}
            observed.append({"case_family": group, "snapshot": snapshot, "key": key,
                             "expected": row, "observed": selected, "matches": row == selected})
        for key in sorted(indexed.keys() - expected_keys, key=str):
            observed.append({"case_family": group, "snapshot": snapshot, "key": key,
                             "expected": None, "observed": indexed[key], "matches": False})

    def result(db, query):
        return json.loads(json.dumps(rows(db, query), default=json_value))

    for snapshot, cutoff_key in (("PRIMARY","primary_recorded_inclusive"),
                                 ("REPLAY","replay_recorded_inclusive"),
                                 ("PRE","pre_restatement_recorded_inclusive"),
                                 ("POST","post_restatement_recorded_inclusive")):
        db, note = run(src, snapshot, cut["effective_exclusive"], cut[cutoff_key])
        run_notes.append(note)
        if snapshot in ("PRE","POST"):
            compare("restatement_trace", [r for r in ref["restatement_trace"] if r["snapshot"]==snapshot],
                    result(db, f"""SELECT 'core:p-fee' source_key,'{snapshot}' snapshot,
                        sum(signed_cents) fee_net_cents,count(*)=2 adjustment_present,
                        max(effective_at) FILTER (WHERE source_key='core:p-correct') adjustment_effective_at
                        FROM financial_event WHERE source_key IN ('core:p-fee','core:p-correct')"""),
                    ["source_key"], snapshot)
            db.close()
            continue
        selected = "primary_visible" if snapshot == "PRIMARY" else "replay_visible"
        compare("ledger", [{k:v for k,v in r.items() if k not in ("primary_visible","replay_visible")}
                           for r in ref["ledger"] if r[selected]], result(db, ledger_query),
                ["source_key"], snapshot)
        compare("customer_all_visible", [r for r in ref["customer_all_visible"] if r["snapshot"]==snapshot],
                result(db, f"SELECT customer_id,'{snapshot}' snapshot,{TOTALS} FROM financial_event GROUP BY customer_id"),
                ["customer_id"], snapshot)
        compare("customer_age", [r for r in ref["customer_age"] if r["snapshot"]==snapshot],
                result(db, f"SELECT '{snapshot}' snapshot,* EXCLUDE(run_id,horizon_end) FROM customer_age"),
                ["customer_id","age_days"], snapshot)
        compare("cohort", [r for r in ref["cohort_realized"] if r["snapshot"]==snapshot],
                result(db, f"""SELECT '{snapshot}' snapshot,channel,signup_month,age_days,cohort_status,
                     registrations,mature_customers,revenue_cents,cost_cents,contribution_cents
                     FROM channel_cohort WHERE model_version='A_v0.3_BASELINE'
                       AND allocation_method='CALENDAR' AND registrations>0"""),
                ["channel","signup_month","age_days"],snapshot)
        compare("forecasts", ref["forecasts"], result(db, """
          SELECT p.customer_id,f.feature_id,f.channel,f.normalized_intent intent,m.scenario,
                 m.model_version fixture_version,CAST(json_extract(m.parameter_payload,
                   '$.multipliers_percent.'||f.channel) AS INTEGER) multiplier_percent,
                 p.age_days,p.expected_cents
          FROM prediction_age p JOIN forecast_model m USING(model_version) JOIN feature_snapshot f USING(customer_id)"""),
                ["customer_id","scenario","age_days"], snapshot)
        if snapshot == "PRIMARY":
            compare("acquisition", [{k:v for k,v in r.items() if k!="link_ids"} for r in ref["acquisition"]],
                    result(db, """SELECT r.registration_id,a.customer_id,t.touch_id,t.campaign_id,
                        coalesce(t.status,e.reason) status FROM registration r LEFT JOIN acquisition a USING(registration_id)
                        LEFT JOIN attribution t USING(customer_id) LEFT JOIN exception_log e ON e.source_id=r.registration_id"""),
                    ["registration_id"],snapshot)
            compare("coverage",ref["coverage"],result(db,"""SELECT coalesce(strftime(a.signup_month,'%Y-%m'),'ALL') period,
                    count(*) FILTER (WHERE t.status='MATCHED') matched,count(*) canonical
                    FROM acquisition a JOIN attribution t USING(customer_id) GROUP BY GROUPING SETS ((a.signup_month),())"""),
                    ["period"],snapshot)
            compare("product_totals", ref["product_totals"],
                    result(db,f"SELECT account_id,{TOTALS} FROM financial_event GROUP BY account_id"),["account_id"],snapshot)
            compare("excluded",ref["excluded"],result(db,"""
                SELECT delivery_id,source_key,'NON_ECONOMIC' reason FROM activity
                WHERE activity_code IN ('DEP_SETTLED','WITHDRAWAL','PURCHASE_SETTLED','PURCHASE_REFUND','LOAN_FUNDING','PRINCIPAL_REPAYMENT','INTEREST_RECEIPT')
                UNION ALL
                SELECT d.delivery_id,d.source_key,CASE WHEN e.reason='LATE_RECORD' THEN 'AFTER_PRIMARY_RECORDED_CUTOFF' ELSE e.reason END
                FROM exception_log e JOIN product_activity_delivery d ON d.delivery_id=e.source_id
                WHERE e.source_table='product_activity_delivery'"""),["delivery_id"],snapshot)
            compare("spend",ref["spend_allocations"],result(db,"""SELECT campaign_id,spend_date,allocated_cents,
                    signup_month,allocation_method method,winner_count,lag_incomplete FROM spend_allocation"""),
                    ["campaign_id","spend_date","signup_month","method"],snapshot)
            compare("spend_reconciliation",ref["spend_reconciliation"],result(db, """
                SELECT *,source_cents-allocated_cents unallocated_cents FROM (
                  SELECT allocation_method method,(SELECT sum(eligible_cents) FROM daily_spend) source_cents,
                    sum(allocated_cents) allocated_cents FROM spend_allocation GROUP BY allocation_method)"""),["method"],snapshot)
            compare("activation",ref["activation"],result(db,"""SELECT customer_id,product,status,source_key qualifying_source_key,activation_at FROM activation"""),
                    ["customer_id","product"],snapshot)
            compare("activation_summary",ref["activation_summary"],result(db,"""
              WITH eligible AS (
                SELECT a.customer_id,strftime(a.signup_month,'%Y-%m') period,t.channel,h.maturity,
                       EXISTS (SELECT 1 FROM activation x WHERE x.customer_id=a.customer_id
                         AND status='QUALIFIED') activated
                FROM acquisition a JOIN attribution t USING(customer_id)
                JOIN customer_age h ON h.customer_id=a.customer_id AND h.age_days=30)
              SELECT period||'_'||coalesce(channel,'ALL') AS "group",
                count(*) FILTER(WHERE maturity='MATURE' AND activated) activated,
                count(*) FILTER(WHERE maturity='MATURE') mature
              FROM eligible GROUP BY GROUPING SETS ((period,channel),(period))
              HAVING period<>'2026-06' OR channel IS NULL"""),["group"],snapshot)
            expected_metrics = []
            for r in ref["march_campaign_and_channel_metrics"]:
                expected_metrics.append(dict(method=r["method"], channel=r["channel"], registrations=r["registrations"],
                    spend_cents=r["spend_cents"],revenue_90_cents=r["revenue_90_cents"],
                    cac_usd=str(exact_ratio(r["cac_cents"]["numerator"],100*r["cac_cents"]["denominator"],8)),
                    revenue_roas=str(exact_ratio(r["roas_90"]["numerator"],r["roas_90"]["denominator"],8))))
            def normalize_decimals(records):
                for rec in records:
                    for name in ("cac_usd","revenue_roas"):
                        if rec.get(name) is not None:
                            rec[name]=str(Decimal(rec[name]).quantize(Decimal("0.00000001")))
                return records
            compare("march_metrics", expected_metrics, normalize_decimals(result(db,"""
                SELECT allocation_method method,channel,registrations,eligible_spend_cents spend_cents,
                revenue_cents revenue_90_cents,cac_usd,revenue_roas FROM channel_cohort
                WHERE signup_month='2025-03-01' AND age_days=90 AND channel<>'UNKNOWN'
                  AND model_version='A_v0.3_BASELINE'""")),["method","channel"],snapshot)
            daily = {(r["campaign_id"],r["date"]) for r in ref["campaign_day_metrics"]}
            compare("operational",ref["campaign_day_metrics"],[r for r in result(db,"""
                SELECT campaign_id,report_date date,eligible_spend_cents spend_cents,registrations,
                CASE WHEN registrations>0 THEN {'numerator':eligible_spend_cents,'denominator':registrations} END cac_cents
                FROM campaign_performance_day""") if (r["campaign_id"],r["date"]) in daily],
                ["campaign_id","date"],snapshot)
            compare("missing_plan_freeze", [{"campaign_id":"F","planned_cents":None,"pace_ratio":None,
                        "pacing_status":"UNAVAILABLE"}],
                result(db,"""SELECT campaign_id,planned_cents,pace_ratio,pacing_status
                     FROM campaign_performance_day WHERE campaign_id='F' AND report_date='2025-03-02'"""),
                ["campaign_id"],snapshot)
            compare("spend_only_freeze", [{"channel":"GOOGLE_ADS","eligible_spend_cents":4200,"registrations":0,
                    "cac_usd":None,"revenue_roas":None,"paid_metric_status":"ZERO_DENOMINATOR"}],
                result(db,"""SELECT channel,eligible_spend_cents,registrations,cac_usd,revenue_roas,paid_metric_status
                  FROM channel_cohort WHERE cohort_status='SPEND_ONLY' AND signup_month='2025-02-01'
                  AND age_days=90 AND allocation_method='CALENDAR' AND model_version='A_v0.3_BASELINE'"""),
                ["channel"],snapshot)
        db.close()
    differences = [r for r in observed if not r["matches"]]
    write_json(output / "controlled_comparison.json", {"reference_sha256": sha256(VALIDATION / "independent_expected.json"),
               "runs": run_notes, "assertion_rows": len(observed), "discrepancies": differences, "results": observed})
    return len(observed), differences


def export_full(db, metadata, output):
    tables = ("acquisition", "attribution", "canonical_activity", "financial_event", "feature_snapshot",
              "forecast_model", "prediction", "prediction_age", "activation", "customer_age",
              "spend_allocation", "channel_cohort", "campaign_performance_day", "exception_log")
    queries = {
        "financial_reconciliation": """
          WITH source_basis AS (
             SELECT product,class,count(*) source_components,
                sum(CASE WHEN basis IS NULL THEN amount_cents ELSE
                    exact_ratio(amount_cents::HUGEINT*(annual_rate*100000000)::HUGEINT,36500000000,0) END)
                    ::BIGINT source_cents
             FROM economic_input WHERE violation IS NULL GROUP BY ALL
          ), ledger AS (
             SELECT p.product,f.class,count(*) FILTER(WHERE f.original_event_id IS NULL) ledger_base_components,
                sum(signed_cents) FILTER(WHERE f.original_event_id IS NULL)::BIGINT ledger_base_cents,
                coalesce(sum(signed_cents) FILTER(WHERE f.original_event_id IS NOT NULL),0)::BIGINT adjustments_cents,
                sum(signed_cents)::BIGINT ledger_net_cents
             FROM financial_event f JOIN product_account p USING(account_id) GROUP BY ALL
          )
          SELECT *,source_components-ledger_base_components component_difference,
                   source_cents+adjustments_cents-ledger_net_cents difference_cents
          FROM source_basis FULL JOIN ledger USING(product,class) ORDER BY product,class
        """,
        "source_disposition": """
          SELECT d.delivery_id,d.source_key,d.account_id,d.activity_code,d.effective_at,d.recorded_at,
                 f.event_id,coalesce(e.reason,
                   CASE WHEN f.event_id IS NOT NULL THEN 'RECOGNIZED'
                        WHEN c.source_key IS NOT NULL THEN 'NON_ECONOMIC'
                        ELSE 'OUTSIDE_EFFECTIVE_WINDOW' END) disposition
          FROM product_activity_delivery d LEFT JOIN canonical_activity c USING(delivery_id)
          LEFT JOIN financial_event f ON f.source_key=c.source_key AND f.run_id=c.run_id
          LEFT JOIN exception_log e ON e.source_table='product_activity_delivery' AND e.source_id=d.delivery_id
          ORDER BY d.delivery_id
        """,
        "marketing_reconciliation": """
          WITH allocated AS (SELECT campaign_id,spend_date,allocation_method,
              sum(allocated_cents)::BIGINT allocated_cents FROM spend_allocation GROUP BY ALL)
          SELECT d.campaign_id,d.spend_date,m.allocation_method,d.recorded_at,d.eligible_cents,
                 coalesce(a.allocated_cents,0) allocated_cents,d.eligible_cents-coalesce(a.allocated_cents,0) difference_cents
          FROM daily_spend d CROSS JOIN (SELECT unnest(['CALENDAR','TOUCH_WEIGHT']) allocation_method) m
          LEFT JOIN allocated a USING(campaign_id,spend_date,allocation_method)
          ORDER BY campaign_id,spend_date,allocation_method
        """,
        "history_reconciliation": """
          WITH check_age AS (
            SELECT h.customer_id,h.age_days,h.revenue_cents,h.cost_cents,
              coalesce(sum(f.signed_cents) FILTER(WHERE f.class='REVENUE'),0) ledger_revenue,
              coalesce(sum(f.signed_cents) FILTER(WHERE f.class='COST'),0) ledger_cost
            FROM customer_age h JOIN acquisition a USING(customer_id)
            LEFT JOIN financial_event f ON f.customer_id=h.customer_id AND f.run_id=h.run_id
               AND f.effective_at>=a.registration_at AND f.effective_at<h.horizon_end
            WHERE h.maturity='MATURE' GROUP BY ALL
          )
          SELECT age_days,count(*) mature_customers,
             sum(revenue_cents)::BIGINT customer_revenue_cents,sum(ledger_revenue)::BIGINT ledger_revenue_cents,
             sum(cost_cents)::BIGINT customer_cost_cents,sum(ledger_cost)::BIGINT ledger_cost_cents,
             count(*) FILTER(WHERE revenue_cents<>ledger_revenue OR cost_cents<>ledger_cost) mismatched_customers
          FROM check_age GROUP BY age_days ORDER BY age_days
        """,
        "cohort_reconciliation": """
          WITH rollup AS (
            SELECT h.age_days,a.signup_month,t.channel,sum(h.revenue_cents)::BIGINT r,sum(h.cost_cents)::BIGINT c
            FROM customer_age h JOIN acquisition a USING(customer_id) JOIN attribution t USING(customer_id)
            GROUP BY ALL
          )
          SELECT g.channel,g.signup_month,g.age_days,g.revenue_cents,g.cost_cents,
                 revenue_cents-r revenue_difference_cents,cost_cents-c cost_difference_cents
          FROM channel_cohort g JOIN rollup USING(age_days,signup_month,channel)
          WHERE g.cohort_status='MATURE' AND g.allocation_method='CALENDAR'
            AND g.model_version='A_v0.3_BASELINE'
          ORDER BY channel,signup_month,age_days
        """,
        "worked_customer_trace": """
          WITH example AS (
           SELECT h.customer_id FROM customer_age h
           JOIN product_account p ON p.owner_identity=(SELECT registration_identity FROM acquisition a
                       JOIN registration r USING(registration_id) WHERE a.customer_id=h.customer_id)
           WHERE h.age_days=90 AND h.maturity='MATURE'
           GROUP BY h.customer_id ORDER BY count(DISTINCT p.product) DESC,h.customer_id LIMIT 1
          )
          SELECT f.customer_id,d.delivery_id,f.source_key,f.event_id,f.account_id,p.product,d.activity_code,
                 d.amount_cents,d.annual_rate,d.balance_kind,f.event_code,f.class,f.signed_cents,
                 f.effective_at, f.recorded_at,o.source_key original_source_key
          """ + LEDGER_JOIN + """
          JOIN product_account p ON p.account_id=f.account_id
          JOIN example x ON x.customer_id=f.customer_id JOIN acquisition a ON a.customer_id=f.customer_id
          WHERE f.effective_at>=a.registration_at AND f.effective_at<a.registration_at+INTERVAL 90 DAY
          ORDER BY f.effective_at,f.source_key
        """,
        "worked_customer_summary": """
          SELECT h.*,f.expected_cents,a.channel,a.campaign_id FROM customer_age h
          JOIN prediction_age f USING(customer_id,age_days) JOIN attribution a USING(customer_id)
          WHERE f.model_version='A_v0.3_BASELINE'
            AND h.customer_id IN (SELECT DISTINCT customer_id FROM worked_customer_trace_view)
          ORDER BY age_days
        """,
        "campaign_monitoring": """
          SELECT * FROM campaign_performance_day WHERE report_date BETWEEN '2025-08-01' AND '2025-08-14'
          ORDER BY campaign_id,report_date
        """,
        "cohort_comparison": """
          SELECT * FROM channel_cohort WHERE cohort_status='MATURE' AND
          signup_month IN ('2025-03-01','2025-09-01') AND age_days IN (30,90,180)
          ORDER BY signup_month,channel,age_days,allocation_method,model_version
        """,
        "scenario_comparison": """
          SELECT b.channel,b.signup_month,b.age_days,b.allocation_method,b.registrations,b.mature_customers,
                 b.eligible_spend_cents,b.contribution_cents,b.expected_comparable_cents baseline_comparable_cents,
                 e.expected_comparable_cents equal_channel_comparable_cents,
                 e.expected_all_cents-b.expected_all_cents change_all_expected_cents,
                 b.expected_all_cents baseline_all_expected_cents,e.expected_all_cents equal_channel_all_expected_cents
          FROM channel_cohort b JOIN channel_cohort e USING(run_id,channel,signup_month,age_days,allocation_method)
          WHERE b.model_version='A_v0.3_BASELINE' AND e.model_version='A_v0.3_EQUAL_CHANNEL' AND b.registrations>0
          ORDER BY channel,signup_month,age_days,allocation_method
        """,
        "allocation_comparison": """
          SELECT channel,signup_month,age_days,b.registrations calendar_registrations,
                 a.registrations touch_registrations,b.eligible_spend_cents calendar_cents,
                 a.eligible_spend_cents touch_cents,b.cac_usd calendar_cac,a.cac_usd touch_cac,
                 b.revenue_roas calendar_roas,a.revenue_roas touch_roas
          FROM (SELECT * FROM channel_cohort WHERE model_version='A_v0.3_BASELINE'
                AND allocation_method='CALENDAR' AND age_days=90) b
          FULL JOIN (SELECT * FROM channel_cohort WHERE model_version='A_v0.3_BASELINE'
                AND allocation_method='TOUCH_WEIGHT' AND age_days=90) a
          USING(run_id,channel,signup_month,age_days,model_version)
          ORDER BY channel,signup_month
        """,
    }
    db.execute("CREATE TEMP VIEW worked_customer_trace_view AS " + queries["worked_customer_trace"])
    row_counts = {}
    for table in tables:
        query = f"SELECT * FROM {table} ORDER BY ALL"
        db.execute(f"COPY ({query}) TO ? (FORMAT PARQUET, COMPRESSION ZSTD)", [str(output / f"{table}.parquet")])
        row_counts[table] = db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    for name, query in queries.items():
        large = name == "source_disposition"
        path = output / f"{name}.{'parquet' if large else 'csv'}"
        db.execute(f"COPY ({query}) TO ? ({'FORMAT PARQUET, COMPRESSION ZSTD' if large else 'FORMAT CSV, HEADER TRUE'})",
                   [str(path)])
    metadata.update(specification_version="1.0", build_version=BUILD, timezone="UTC",
                    duckdb_version=duckdb.__version__, threads=4, output_row_counts=row_counts)
    metadata["financial_reconciliation"] = rows(db, queries["financial_reconciliation"])
    metadata["history_reconciliation"] = rows(db, queries["history_reconciliation"])
    metadata["cohort_reconciliation_mismatches"] = db.execute(
        f"SELECT count(*) FROM ({queries['cohort_reconciliation']}) WHERE revenue_difference_cents<>0 OR cost_difference_cents<>0"
    ).fetchone()[0]
    metadata["spend_reconciliation"] = rows(db, f"""SELECT allocation_method,sum(eligible_cents)::BIGINT source_cents,
       sum(allocated_cents)::BIGINT allocated_cents,sum(abs(difference_cents))::BIGINT absolute_difference_cents
       FROM ({queries['marketing_reconciliation']}) GROUP BY allocation_method ORDER BY allocation_method""")
    metadata["exception_counts"] = rows(db, "SELECT reason,count(*) count FROM exception_log GROUP BY reason ORDER BY reason")
    metadata["output_files"] = {path.name: sha256(path) for path in sorted(output.iterdir()) if path.is_file()
                                and path.name != "pipeline_manifest.json"}
    write_json(output / "pipeline_manifest.json", metadata)
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/analytical_outputs")
    parser.add_argument("--controlled-only", action="store_true")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    assertions, differences = controlled(args.output)
    print(f"Controlled fixture: {assertions} comparisons, {len(differences)} discrepancies", flush=True)
    if differences or args.controlled_only:
        return bool(differences)
    manifest = json.loads((SOURCES / "manifest_v1.0.json").read_text())
    db, metadata = run(SOURCES, "FULL_PRIMARY_V1", manifest["effective_cutoff_exclusive"],
                       manifest["recorded_cutoff_inclusive"])
    metadata["controlled_comparisons"] = assertions
    metadata["controlled_discrepancies"] = len(differences)
    result = export_full(db, metadata, args.output)
    print(json.dumps({"rows": result["output_row_counts"],"spend":result["spend_reconciliation"]},indent=2))
    db.close()
    differences = (
        any(row["difference_cents"] or row["component_difference"] for row in result["financial_reconciliation"])
        or any(row["mismatched_customers"] for row in result["history_reconciliation"])
        or any(row["absolute_difference_cents"] for row in result["spend_reconciliation"])
        or result["cohort_reconciliation_mismatches"] != 0
    )
    return differences


if __name__ == "__main__":
    raise SystemExit(main())
