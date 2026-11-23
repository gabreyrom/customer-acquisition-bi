"""Independently reconcile full source records to Workstream C exports."""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/synthetic_sources"
OUT = ROOT / "data/analytical_outputs"
CUT = "2026-07-01T00:00:00Z"
AGES = (30, 90, 180, 365)
PRINCIPAL = set("DEP_SETTLED WITHDRAWAL PURCHASE_SETTLED PURCHASE_REFUND LOAN_FUNDING PRINCIPAL_REPAYMENT INTEREST_RECEIPT".split())
REVENUE = set("SAV_TREASURY_INCOME SAV_FEE DEBIT_INTERCHANGE DEBIT_FEE CREDIT_INTERCHANGE CREDIT_INTEREST CREDIT_FEE PERSONAL_INTEREST PERSONAL_FEE MORTGAGE_INTEREST MORTGAGE_FEE".split())
COST = set("SAV_DEPOSIT_INTEREST SAV_SERVICE DEBIT_PROCESSING DEBIT_REWARD DEBIT_FRAUD DEBIT_SERVICE CREDIT_FUNDING CREDIT_LOSS CREDIT_PROCESSING CREDIT_REWARD CREDIT_SERVICE PERSONAL_FUNDING PERSONAL_SERVICE PERSONAL_COLLECTION PERSONAL_LOSS MORTGAGE_FUNDING MORTGAGE_ORIGINATION MORTGAGE_SERVICE MORTGAGE_LOSS".split())
# Independently transcribed annual product expectations in cents from A (including BORROW).
TERMS = {"EVERYDAY": (990,1560,1950,450,180), "BORROW": (450,720,2925,2250,1080),
         "UNKNOWN": (630,1080,1950,900,360)}
FRACTIONS = ((7,6,3,1,0),(22,23,17,10,5),(47,48,43,38,25),(100,100,100,100,100))
MULTIPLIER = {"GOOGLE_ADS":100,"META_ADS":95,"PAID_AFFILIATES":90,"UNKNOWN":100}


def source(table):
    with gzip.open(SRC / (table + ".jsonl.gz"), "rt") as handle:
        yield from map(json.loads, handle)


def dt(t):
    return datetime.fromisoformat(t)


def half_up(value):
    positive = abs(value)
    n, d = positive.numerator, positive.denominator
    return ((2*n+d)//(2*d)) * (-1 if value < 0 else 1)


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def audit():
    db = duckdb.connect(config={"threads": 4})
    db.execute("SET TimeZone='UTC'")
    manifest = json.loads((SRC / "manifest_v1.0.json").read_text())
    for name,item in manifest["files"].items():
        assert sha(SRC/name) == item["sha256"], name
    run = json.loads((OUT / "pipeline_manifest.json").read_text())
    for name,digest in run["output_files"].items():
        assert sha(OUT/name) == digest, name

    def query(sql):
        return db.execute(sql).fetchall()

    links = defaultdict(list)
    touches = defaultdict(list)
    features = defaultdict(list)
    campaign = {r["campaign_id"]:r["channel"] for r in source("campaign")}
    for row in source("identity_link"):
        links[row["identity_key"]].append(row)
    for row in source("marketing_touch"):
        touches[row["visitor_identity"]].append(row)
    for row in source("registration_feature"):
        features[row["registration_id"]].append(row)

    def owners(key, boundary):
        # Full generated source uses distinct candidate claims, without retractions.
        return {r["canonical_customer_id"] for r in links[key] if r["link_state"] == "CANDIDATE"
                and r["recorded_at"] <= boundary and r["effective_from"] <= boundary
                and (not r["effective_to"] or boundary < r["effective_to"])}

    acquisitions, attribution, forecasts, person_by_identity = {}, {}, {}, {}
    touch_winners = defaultdict(Counter)
    for row in source("registration"):
        instant = row["registration_at"]
        if row["state"] != "VALID" or row["recorded_at"] > CUT or instant >= CUT:
            continue
        person = owners(row["registration_identity"], instant)
        if len(person) != 1:
            continue
        customer = next(iter(person))
        assert customer not in acquisitions
        acquisitions[customer] = (row["registration_id"], instant)
        person_by_identity[row["registration_identity"]] = customer
        visitor = owners(row["visitor_identity"], instant)
        start = dt(instant) - timedelta(days=30)
        candidates = [t for t in touches[row["visitor_identity"]]
                      if t["state"] == "ELIGIBLE" and t["recorded_at"] <= instant
                      and start <= dt(t["touched_at"]) < dt(instant)] if visitor == person else []
        best = min(sorted(candidates,key=lambda t:t["touch_id"]),
                   key=lambda t:-dt(t["touched_at"]).timestamp(),default=None)
        if best:
            cid, tid = best["campaign_id"], best["touch_id"]
            channel, status = campaign[cid], "MATCHED"
            touch_winners[(cid,best["touched_at"][:10])][instant[:7]+"-01"] += 1
        else:
            cid = tid = None
            channel = "UNKNOWN"
            status = ("AMBIGUOUS_VISITOR_LINK" if len(visitor)>1 else "MISSING_VISITOR_LINK"
                      if visitor!=person else "NO_ELIGIBLE_TOUCH")
        attribution[customer] = (tid,cid,channel,status)
        eligible = [f for f in features[row["registration_id"]]
                    if f["effective_at"]<=instant and f["recorded_at"]<=instant]
        f = max(sorted(eligible,key=lambda r:r["feature_id"]),
                key=lambda r:(r["effective_at"],r["recorded_at"]),default=None)
        intent = f["intent"] if f and f["intent"] in TERMS else "UNKNOWN"
        values = [sum(a*b for a,b in zip(TERMS[intent],fractions)) for fractions in FRACTIONS]
        for scenario,m in (("BASELINE",MULTIPLIER[channel]),("EQUAL_CHANNEL",100)):
            for age,n in zip(AGES,values):
                forecasts[(customer,scenario,age)] = (half_up(Fraction(n*m,10000)), f["feature_id"] if f else None, intent)
    assert acquisitions == {c:(r,t.isoformat().replace("+00:00","Z")) for c,r,t in query(
        "SELECT customer_id,registration_id,registration_at FROM read_parquet('data/analytical_outputs/acquisition.parquet')")}
    assert attribution == {c:(t,p,ch,s) for c,t,p,ch,s in query(
        "SELECT customer_id,touch_id,campaign_id,channel,status FROM read_parquet('data/analytical_outputs/attribution.parquet')")}
    assert forecasts == {(c,s,a):(v,f,i) for c,s,a,v,f,i in query("""
       SELECT p.customer_id,replace(p.model_version,'A_v0.3_',''),p.age_days,p.expected_cents,f.feature_id,f.normalized_intent
       FROM read_parquet('data/analytical_outputs/prediction_age.parquet') p
       JOIN read_parquet('data/analytical_outputs/feature_snapshot.parquet') f USING(customer_id)""")}
    assert query("""SELECT count(*) FROM read_parquet('data/analytical_outputs/feature_snapshot.parquet')
                    WHERE feature_available_at>feature_cutoff""")[0][0] == 0

    spend_allocations = {}
    spend_total = 0
    for row in source("campaign_day"):
        campaign_id, day, amount = row["campaign_id"],row["spend_date"],row["eligible_cents"]
        spend_total += amount
        month = day[:7]+"-01"
        spend_allocations[(campaign_id,day,"CALENDAR",month)] = amount
        winners = touch_winners[(campaign_id,day)]
        if not winners:
            spend_allocations[(campaign_id,day,"TOUCH_WEIGHT",month)] = amount
            continue
        exact = {m:Fraction(amount*n,sum(winners.values())) for m,n in winners.items()}
        base = {m:int(v) for m,v in exact.items()}
        order = sorted(base,key=lambda m:(base[m]-exact[m],m))
        for target in order[:amount-sum(base.values())]:
            base[target] += 1
        for target,v in base.items():
            spend_allocations[(campaign_id,day,"TOUCH_WEIGHT",target)] = v
    assert spend_allocations == {(c,d.isoformat(),m,s.isoformat()):v for c,d,m,s,v in query("""
       SELECT campaign_id,spend_date,allocation_method,signup_month,allocated_cents
       FROM read_parquet('data/analytical_outputs/spend_allocation.parquet')""")}
    for method in ("CALENDAR", "TOUCH_WEIGHT"):
        assert sum(v for k,v in spend_allocations.items() if k[2]==method)==spend_total

    accounts = {r["account_id"]:(person_by_identity[r["owner_identity"]],r["product"],r["opened_at"])
                for r in source("product_account")}
    observed = db.execute("""
      SELECT f.source_key,d.delivery_id,f.account_id,f.customer_id,f.event_code,f.class,f.signed_cents,
             f.effective_at,f.recorded_at,f.original_event_id
      FROM read_parquet('data/analytical_outputs/financial_event.parquet') f
      JOIN read_parquet('data/analytical_outputs/canonical_activity.parquet') d USING(run_id,source_key)
      ORDER BY d.delivery_id""")
    next_row = observed.fetchone()
    originals = {}
    remaining = {}
    totals = defaultdict(Counter)
    dispositions = Counter()
    history = defaultdict(Counter)
    worked = defaultdict(Counter)
    horizons = {c:[dt(t)+timedelta(days=a) for a in AGES] for c,(_,t) in acquisitions.items()}
    for row in source("product_activity_delivery"):
        key, code = row["source_key"], row["activity_code"]
        if row["recorded_at"]>CUT:
            dispositions["LATE_RECORD"]+=1
            continue
        if key in originals:
            dispositions["DUPLICATE_DELIVERY"]+=1
            continue
        owner,product,opened = accounts[row["account_id"]]
        effective = row["effective_at"]
        assert opened<=effective<CUT
        originals[key] = row
        if code in PRINCIPAL:
            dispositions["NON_ECONOMIC"]+=1
            continue
        cents = row["amount_cents"]
        parent = None
        if code == "ADJUSTMENT":
            original = originals[row["original_source_key"]]
            code = original["activity_code"]
            assert code==row["component"] and original["account_id"]==row["account_id"]
            parent = original["source_key"]+"/"+code
            assert remaining[parent]>=cents
            remaining[parent] -= cents
            cents = -cents
            if row["adjustment_kind"]=="RESTATEMENT_REDUCTION":
                effective=original["effective_at"]
        elif row["annual_rate"]:
            cents=half_up(Fraction(cents)*Fraction(row["annual_rate"])/365)
        if not parent:
            remaining[key+"/"+code]=cents
        assert code in REVENUE or code in COST, code
        cls = "REVENUE" if code in REVENUE else "COST"
        expected = (key,row["delivery_id"],row["account_id"],owner,code,cls,cents,dt(effective),dt(row["recorded_at"]),parent)
        assert next_row == expected, (expected,next_row)
        next_row = observed.fetchone()
        dispositions["RECOGNIZED"]+=1
        totals[product][cls]+=cents
        for i,end in enumerate(horizons[owner]):
            if end<=dt(CUT) and dt(acquisitions[owner][1])<=dt(effective)<end:
                history[owner,AGES[i]][cls]+=cents
                if owner=="C02703" and AGES[i]==90:
                    worked[product][cls]+=cents
                    worked[product]["events"]+=1
    assert next_row is None
    expected_hist = {}
    for customer, ends in horizons.items():
        for age,end in zip(AGES,ends):
            r,c = history[customer,age]["REVENUE"],history[customer,age]["COST"]
            expected_hist[customer,age]=("MATURE",r,c,r-c) if end<=dt(CUT) else ("PENDING",None,None,None)
    assert expected_hist == {(c,a):(m,r,k,n) for c,a,m,r,k,n in query("""
        SELECT customer_id,age_days,maturity,revenue_cents,cost_cents,contribution_cents
        FROM read_parquet('data/analytical_outputs/customer_age.parquet')""")}
    assert dispositions==dict(query("SELECT disposition,count(*) FROM read_parquet('data/analytical_outputs/source_disposition.parquet') GROUP BY 1"))

    cohort = defaultdict(Counter)
    for (customer,age),(state,r,c,n) in expected_hist.items():
        month = acquisitions[customer][1][:7]+"-01"
        ch = attribution[customer][2]
        line=cohort[ch,month,age]
        line["count"]+=1
        if state=="MATURE":
            line.update({"mature":1,"r":r,"c":c,"n":n})
            line["base"]+=forecasts[customer,"BASELINE",age][0]
            line["equal"]+=forecasts[customer,"EQUAL_CHANNEL",age][0]
    confirmed_rows=0
    for ch,month,age,scenario,status,n,m,r,c,net,f in query("""
       SELECT channel,signup_month,age_days,model_version,cohort_status,registrations,mature_customers,
              revenue_cents,cost_cents,contribution_cents,expected_comparable_cents
       FROM read_parquet('data/analytical_outputs/channel_cohort.parquet')
       WHERE allocation_method='CALENDAR' AND registrations>0"""):
        day = month.isoformat()
        future_month = (month.replace(day=28)+timedelta(days=4)).replace(day=1)
        mature = future_month+timedelta(days=age) <= dt(CUT).date()
        x=cohort[ch,day,age]
        assert (n,m)==(x["count"],x["mature"])
        values=(x["r"],x["c"],x["n"],x["base" if scenario.endswith("BASELINE") else "equal"])
        assert (status,r,c,net,f)==(("MATURE",*values) if mature else ("PENDING",None,None,None,None))
        confirmed_rows+=1
    assert confirmed_rows==2*len(cohort)
    fore_totals=defaultdict(Counter)
    for (customer,scenario,age),(value,_,_) in forecasts.items():
        if age==365:
            fore_totals[attribution[customer][2]][scenario]+=value
            if scenario=="BASELINE":
                fore_totals[attribution[customer][2]]["customers"]+=1
    checks = {"status":"MATCHED", "source_delivery_disposition":dict(dispositions),
              "product_totals_cents":{k:dict(v) for k,v in totals.items()},
              "revenue_cents":sum(v["REVENUE"] for v in totals.values()),
              "cost_cents":sum(v["COST"] for v in totals.values()),
              "eligible_spend_cents_per_method":spend_total,
              "acquisitions":len(acquisitions), "attribution_counts":dict(Counter(t[3] for t in attribution.values())),
              "allocation_rows_matched":len(spend_allocations),"forecast_rows_matched":len(forecasts),
              "history_rows_matched":len(expected_hist),"calendar_cohort_rows_matched":confirmed_rows,
              "worked_90d_by_product_cents":{k:dict(v) for k,v in worked.items()},
              "forecast_365_by_channel":{k:dict(v) for k,v in fore_totals.items()}}
    checks["contribution_cents"]=checks["revenue_cents"]-checks["cost_cents"]
    print(json.dumps(checks,indent=2))


if __name__=="__main__":
    audit()
