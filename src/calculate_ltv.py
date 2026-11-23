"""Score frozen acquisition features with exact arithmetic from Workstream A v0.3."""

from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json

PRODUCTS = {
    "SAVINGS": (55, 25, 35, 1800, (7, 22, 47, 100)),
    "DEBIT": (65, 30, 45, 2400, (6, 23, 48, 100)),
    "CREDIT": (30, 45, 30, 6500, (3, 17, 43, 100)),
    "PERSONAL": (5, 25, 10, 9000, (1, 10, 38, 100)),
    "MORTGAGE": (1, 6, 2, 18000, (0, 5, 25, 100)),
}
BASELINE = {"GOOGLE_ADS": 100, "META_ADS": 95, "PAID_AFFILIATES": 90, "UNKNOWN": 100}
AGES = (30, 90, 180, 365)
INTENTS = ("EVERYDAY", "BORROW", "UNKNOWN")


def score(db):
    db.execute("""
    INSERT INTO feature_snapshot
    SELECT a.customer_id,a.registration_at,t.channel,
     CASE WHEN f.intent IN ('EVERYDAY','BORROW') THEN f.intent ELSE 'UNKNOWN' END AS intent_normalized,
     f.feature_id,f.recorded_at,
     CASE WHEN f.feature_id IS NOT NULL THEN CASE WHEN f.intent IN ('EVERYDAY','BORROW') THEN 'VALID' ELSE 'INVALID' END
          WHEN EXISTS(SELECT 1 FROM registration_feature x WHERE x.registration_id=a.registration_id
            AND x.recorded_at>a.registration_at AND x.recorded_at<=r.recorded_cutoff) THEN 'LATE' ELSE 'MISSING' END,
     sha256(to_json(list_value(a.customer_id,a.registration_at::VARCHAR,t.channel, intent_normalized,
                               f.feature_id,f.recorded_at::VARCHAR,t.touch_id))::VARCHAR)
    FROM acquisition a JOIN attribution t USING(customer_id) CROSS JOIN run_manifest r
    LEFT JOIN LATERAL (
     SELECT * FROM registration_feature f WHERE f.registration_id=a.registration_id
       AND f.effective_at<=a.registration_at AND f.recorded_at<=a.registration_at
     ORDER BY f.effective_at DESC,f.recorded_at DESC,f.feature_id LIMIT 1
    ) f ON true
    """)
    features = db.execute("""SELECT customer_id,channel,normalized_intent,feature_cutoff,recorded_cutoff
                              FROM feature_snapshot CROSS JOIN run_manifest ORDER BY customer_id""").fetchall()
    for scenario, multipliers in (("BASELINE", BASELINE), ("EQUAL_CHANNEL", dict.fromkeys(BASELINE, 100))):
        version = "A_v0.3_" + scenario
        payload = json.dumps({"intent_order": INTENTS, "ages": AGES, "product_inputs": PRODUCTS,
                              "multipliers_percent": multipliers}, sort_keys=True)
        db.execute("INSERT INTO forecast_model VALUES (?,?,?,?,?)", [
            version, scenario, hashlib.sha256(payload.encode()).hexdigest(), payload,
            None if scenario == "BASELINE" else "A_v0.3_BASELINE"])
        predictions, trajectories = [], []
        for customer, channel, intent, cutoff, asof in features:
            index = INTENTS.index(intent)
            cents = [
                int((Decimal(sum(p[index] * p[3] * p[4][i] for p in PRODUCTS.values())
                             * multipliers[channel]) / 1_000_000).quantize(Decimal(1), rounding=ROUND_HALF_UP))
                for i in range(len(AGES))
            ]
            predictions.append((customer, version, cutoff, asof, cents[-1]))
            trajectories.extend((customer, version, age, amount) for age, amount in zip(AGES, cents))
        for table, rows in (("prediction", predictions), ("prediction_age", trajectories)):
            if rows:
                columns = [c[0] for c in db.execute(f"DESCRIBE {table}").fetchall()]
                db.execute(f"INSERT INTO {table} SELECT unnest($1, recursive := true)",
                           [[dict(zip(columns, row)) for row in rows]])
