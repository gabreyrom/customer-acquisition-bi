"""Generate only the nine frozen v1.0 source relations as deterministic JSONL gzip."""

import argparse
from contextlib import ExitStack
from datetime import date, timedelta
import gzip
import hashlib
import io
import json
from pathlib import Path
import random

VERSION = "1.0.0"
SEED = 6362025
CUSTOMERS = 5000
START = date(2025, 1, 1)
END = date(2026, 7, 1)
DAY = timedelta(days=1)
CHANNELS = ("GOOGLE_ADS", "META_ADS", "PAID_AFFILIATES")
PRODUCTS = ("SAVINGS", "DEBIT", "CREDIT", "PERSONAL", "MORTGAGE")
FIELDS = {
    "campaign": "campaign_id channel active_from active_through",
    "campaign_day": "campaign_id spend_date recorded_at actual_cents eligible_cents planned_cents",
    "campaign_budget": "campaign_id period_start period_kind recorded_at period_end_exclusive budget_cents target_cac_cents target_activation",
    "registration": "registration_id registration_identity visitor_identity registration_at recorded_at state",
    "identity_link": "identity_link_id identity_key canonical_customer_id effective_from effective_to recorded_at link_state",
    "marketing_touch": "touch_id visitor_identity campaign_id touched_at recorded_at state",
    "registration_feature": "feature_id registration_id intent effective_at recorded_at",
    "product_account": "account_id owner_identity product opened_at closed_at recorded_at",
    "product_activity_delivery": "delivery_id source_key account_id activity_code effective_at recorded_at state amount_cents annual_rate balance_kind original_source_key adjustment_kind component",
}
ASSUMPTIONS = {
    "acquisition": "Exactly 5000 canonical signups, uniformly sampled days with random daytime hours. Six campaigns split across three channels. Paid touch probabilities reflect campaign mix only; product behavior is independent of channel.",
    "intent": "EVERYDAY, BORROW and no observed intent sampled at 56%, 29% and 15%. Product adoption depends on submitted intent, with a 12% no-product segment. Source adoption rates are generation assumptions distinct from frozen model parameters.",
    "spend": "Complete daily calendar across six campaigns with independent campaign-level plans and bounded spend noise, plus selected missing plan days, zero spend days and unassigned spend days.",
    "products": "Savings and revolving credit emit daily balance bases during simulated active balance periods. Personal loans and mortgages emit daily performing and funding bases until cutoff or payoff. Cash and posted economic inputs are separate.",
    "losses": "Confirmed principal charge-off and optional recovery. No expected-loss provisions. Source recovery plus other reductions are capped at original amount.",
    "exceptions": "Index-addressed missing/ambiguous visitor links, no touch, late touch, late intent, missing/ambiguous signup identity, re-delivery, late fee, partial refund and fee restatement. Audit file includes source keys for deliberately injected integration exceptions.",
}


def stamp(day, clock="00:00:00"):
    return f"{day.isoformat()}T{clock}Z"


def dates(start, end):
    return (start + n * DAY for n in range((end - start).days))


def sha256(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


class Sources:
    def __init__(self, output, stack):
        self.handles = {}
        self.counts = dict.fromkeys(FIELDS, 0)
        self.keys = {name: columns.split() for name, columns in FIELDS.items()}
        for name in FIELDS:
            raw = stack.enter_context((output / f"{name}.jsonl.gz").open("wb"))
            zipped = stack.enter_context(gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0))
            self.handles[name] = stack.enter_context(io.TextIOWrapper(zipped, encoding="utf-8", newline="\n"))
        self.exceptions = []

    def row(self, name, *values):
        payload = dict(zip(self.keys[name], values, strict=True))
        self.handles[name].write(json.dumps(payload, separators=(",", ":")) + "\n")
        self.counts[name] += 1

    def exception(self, kind, table, key):
        self.exceptions.append({"kind": kind, "source_table": table, "source_key": key})

    def activity(self, account, code, day, amount, *, rate=None, basis=None,
                 original=None, adjustment=None, component=None, state="POSTED",
                 recorded=None, duplicate=False):
        number = self.counts["product_activity_delivery"] + 1
        key = f"core:E{number:08d}"
        payload = (key, account, code, stamp(day, "21:00:00"),
                   recorded or stamp(day, "23:00:00"), state, amount, rate, basis,
                   original, adjustment, component)
        self.row("product_activity_delivery", f"D{number:08d}", *payload)
        if duplicate:
            self.row("product_activity_delivery", f"D{number + 1:08d}", *payload)
            self.exception("DUPLICATE_DELIVERY", "product_activity_delivery", key)
        return key


def balances(out, account, day, amount, *rules):
    for code, rate, basis in rules:
        out.activity(account, code, day, amount, rate=rate, basis=basis)


def card_activity(out, rng, account, day, prefix, amount, refund):
    purchase = out.activity(account, "PURCHASE_SETTLED", day, amount, state="SETTLED")
    interchange = max(1, amount * (17 if prefix == "CREDIT" else 13) // 1000)
    revenue = out.activity(account, f"{prefix}_INTERCHANGE", day, interchange, state="SETTLED")
    out.activity(account, f"{prefix}_PROCESSING", day, 25 + amount // 500)
    reward = max(1, amount // 140)
    cost = out.activity(account, f"{prefix}_REWARD", day, reward)
    if refund and day + 2 * DAY < END:
        later = day + 2 * DAY
        out.activity(account, "PURCHASE_REFUND", later, amount // 2,
                     original=purchase, state="SETTLED")
        for original, component, base in ((revenue, f"{prefix}_INTERCHANGE", interchange),
                                          (cost, f"{prefix}_REWARD", reward)):
            if base >= 2:
                out.activity(account, "ADJUSTMENT", later, base // 2, original=original,
                             adjustment="LATER_REDUCTION", component=component)


def saving(out, rng, account, begin, customer):
    balance = rng.randrange(3000, 300000, 100)
    end = min(END, begin + rng.randint(45, 105) * DAY)
    out.activity(account, "DEP_SETTLED", begin, balance, state="SETTLED")
    for day in dates(begin, end):
        if day > begin and (day - begin).days % 30 == 0:
            deposit = rng.randrange(1000, 30000, 100)
            out.activity(account, "DEP_SETTLED", day, deposit, state="SETTLED")
            balance += deposit
        balances(out, account, day, balance,
                 ("SAV_TREASURY_INCOME", "0.073", "SAV_SETTLED_TREASURY"),
                 ("SAV_DEPOSIT_INTEREST", "0.0365", "SAV_SETTLED_DEPOSITOR"))
    if end < END:
        out.activity(account, "WITHDRAWAL", end, balance, state="SETTLED")
    out.activity(account, "SAV_SERVICE", begin, rng.randint(35, 180))
    if rng.random() < .25 or customer % 97 == 0:
        late = customer % 97 == 0
        key = out.activity(account, "SAV_FEE", begin, 100,
                           recorded=stamp(END + 2 * DAY) if late else None,
                           duplicate=customer % 29 == 0)
        if late:
            out.exception("AFTER_RECORDED_CUTOFF", "product_activity_delivery", key)


def credit(out, rng, account, begin):
    revolving = rng.randrange(25000, 180000, 100)
    card_activity(out, rng, account, begin, "CREDIT", revolving, False)
    duration = rng.randint(35, 95)
    stop = min(END, begin + duration * DAY)
    chargeoff = rng.random() < .14
    for day in dates(begin, stop):
        balances(out, account, day, revolving,
                 ("CREDIT_INTEREST", "0.219", "CREDIT_PERFORMING_REVOLVING"),
                 ("CREDIT_FUNDING", "0.073", "CREDIT_FUNDED"))
    if stop < END and chargeoff:
        key = out.activity(account, "CREDIT_LOSS", stop, revolving, state="CONFIRMED")
        recovery = stop + rng.randint(10, 40) * DAY
        if recovery < END and rng.random() < .65:
            out.activity(account, "ADJUSTMENT", recovery, revolving // 5,
                         original=key, adjustment="RECOVERY", component="CREDIT_LOSS",
                         state="CONFIRMED")
    elif stop < END:
        out.activity(account, "PRINCIPAL_REPAYMENT", stop, revolving, state="SETTLED")


def loan(out, rng, account, begin, product):
    mortgage = product == "MORTGAGE"
    principal = (rng.randrange(8000000, 36000000, 10000) if mortgage
                 else rng.randrange(50000, 950000, 5000))
    out.activity(account, "LOAN_FUNDING", begin, principal, state="SETTLED")
    fee = principal // (200 if mortgage else 100)
    fee_key = out.activity(account, f"{product}_FEE", begin, fee)
    if mortgage:
        out.activity(account, "MORTGAGE_ORIGINATION", begin, rng.randint(35000, 110000))
    else:
        out.activity(account, "PERSONAL_SERVICE", begin, rng.randint(80, 250))
    correction_at = begin + 12 * DAY
    if correction_at < END and rng.random() < .14:
        out.activity(account, "ADJUSTMENT", correction_at, fee // 5, original=fee_key,
                     component=f"{product}_FEE", adjustment="RESTATEMENT_REDUCTION")
    payment = max(1, principal // (rng.randint(150, 300) if mortgage else rng.randint(6, 24)))
    annual_interest = "0.073" if mortgage else "0.146"
    annual_funding = "0.0365" if mortgage else "0.073"
    performing = f"{product}_PERFORMING_PRINCIPAL"
    for day in dates(begin, END):
        age = (day - begin).days
        if age and age % 30 == 0:
            cash = min(payment, principal)
            out.activity(account, "PRINCIPAL_REPAYMENT", day, cash, state="SETTLED")
            principal -= cash
        if principal == 0:
            break
        balances(out, account, day, principal,
                 (f"{product}_INTEREST", annual_interest, performing),
                 (f"{product}_FUNDING", annual_funding, f"{product}_FUNDED"))


def generate(output, seed):
    output.mkdir(parents=True, exist_ok=True)
    rng = random.Random(seed)
    campaigns = [(f"{prefix}{i}", channel) for prefix, channel in zip("GMF", CHANNELS) for i in (1, 2)]
    with ExitStack() as stack:
        out = Sources(output, stack)
        account_counts = dict.fromkeys(PRODUCTS, 0)
        accounts_per_customer = []
        for j, (cid, channel) in enumerate(campaigns):
            out.row("campaign", cid, channel, START.isoformat(), None)
            plan = (12000, 8500, 14500, 9000, 10000, 7500)[j]
            for day in dates(START, END):
                month = day.replace(day=1)
                next_month = (month.replace(day=28) + 4 * DAY).replace(day=1)
                if day.day == 1:
                    out.row("campaign_budget", cid, str(month), "MONTH", stamp(month),
                            str(next_month), plan * (next_month - month).days, 21000, "0.40")
                actual = 0 if (day - START).days % 59 == j else rng.randint(plan * 7 // 10, plan * 13 // 10)
                missing_plan = (day - START).days % 103 == j
                out.row("campaign_day", cid, str(day), stamp(day, "23:30:00"),
                        actual, actual, None if missing_plan else plan)
                if missing_plan:
                    out.exception("MISSING_PLAN", "campaign_day", f"{cid}/{day}")
        for n in range(1, CUSTOMERS + 1):
            cid, rid, reg, visitor = f"C{n:05d}", f"R{n:05d}", f"reg:{n:05d}", f"web:{n:05d}"
            signup = START + rng.randrange((END - START).days) * DAY
            instant = stamp(signup, f"{rng.randint(9, 18):02d}:00:00")
            out.row("registration", rid, reg, visitor, instant, instant, "VALID")
            out.row("identity_link", f"L{n:05d}R", reg, cid, instant, None, instant, "CANDIDATE")
            ambiguous = n % 113 == 0
            if n % 31:
                out.row("identity_link", f"L{n:05d}V", visitor, cid, stamp(START), None, stamp(START), "CANDIDATE")
            else:
                out.exception("MISSING_VISITOR_LINK", "registration", rid)
            if ambiguous and n % 31:
                other = f"C{n % CUSTOMERS + 1:05d}"
                out.row("identity_link", f"L{n:05d}X", visitor, other, stamp(START), None, stamp(START), "CANDIDATE")
                out.exception("AMBIGUOUS_VISITOR_LINK", "registration", rid)
            if n % 17:
                selected = rng.choices(campaigns, weights=(22, 13, 23, 15, 17, 10))[0][0]
                touch_date = max(START, signup - rng.randint(0, 19) * DAY)
                touch = stamp(touch_date, "07:30:00")
                late_touch = n % 127 == 0
                out.row("marketing_touch", f"T{n:05d}W", visitor, selected, touch,
                        stamp(signup + DAY) if late_touch else touch, "ELIGIBLE")
                if late_touch:
                    out.exception("LATE_TOUCH", "marketing_touch", f"T{n:05d}W")
                if touch_date > START:
                    earlier = stamp(touch_date - DAY, "07:00:00")
                    out.row("marketing_touch", f"T{n:05d}E", visitor, rng.choice(campaigns)[0], earlier, earlier, "ELIGIBLE")
            else:
                out.exception("NO_TRACKED_TOUCH", "registration", rid)
            intent = rng.choices(("EVERYDAY", "BORROW", None), weights=(56, 29, 15))[0]
            if intent is not None:
                late_feature = n % 79 == 0
                out.row("registration_feature", f"I{n:05d}", rid, intent, instant,
                        stamp(signup + DAY) if late_feature else instant)
                if late_feature:
                    out.exception("LATE_INTENT", "registration_feature", f"I{n:05d}")
            holdings = 0
            if rng.random() >= .12:
                chances = (.39, .42, .26, .21, .065) if intent == "BORROW" else (.55, .58, .30, .10, .028)
                for k, product in enumerate(PRODUCTS):
                    begin = signup + rng.randint(1, 48 if k >= 3 else 22) * DAY
                    if rng.random() >= chances[k] or begin >= END:
                        continue
                    account = f"A{n:05d}{k}"
                    opened = stamp(begin, "08:00:00")
                    out.row("product_account", account, reg, product, opened, None, opened)
                    account_counts[product] += 1
                    holdings += 1
                    if product == "SAVINGS":
                        saving(out, rng, account, begin, n)
                    elif product == "DEBIT":
                        for _ in range(rng.randint(1, 5)):
                            day = begin + rng.randint(0, 65) * DAY
                            if day < END:
                                card_activity(out, rng, account, day, "DEBIT", rng.randint(300, 24000), rng.random() < .17)
                    elif product == "CREDIT":
                        credit(out, rng, account, begin)
                    else:
                        loan(out, rng, account, begin, product)
            accounts_per_customer.append(holdings)
        # Two intake exceptions preserve the 5000 uniquely resolvable signups.
        instant = stamp(date(2025, 6, 15), "12:00:00")
        for kind, tag in (("IDENTITY_MISSING", "missing"), ("IDENTITY_AMBIGUOUS", "ambiguous")):
            out.row("registration", f"RX-{tag}", f"reg:{tag}", None, instant, instant, "VALID")
            out.exception(kind, "registration", f"RX-{tag}")
        for i in (1, 2):
            out.row("identity_link", f"LX-{i}", "reg:ambiguous", f"C{i:05d}", instant, None, instant, "CANDIDATE")
    audit = output / "expected_source_exceptions.json"
    audit.write_text(json.dumps(out.exceptions, indent=2) + "\n", encoding="utf-8")
    files = {f"{name}.jsonl.gz": {"rows": n, "sha256": sha256(output / f"{name}.jsonl.gz")} for name, n in out.counts.items()}
    files[audit.name] = {"rows": len(out.exceptions), "sha256": sha256(audit)}
    manifest = {
        "specification_version": "1.0", "generator_version": VERSION, "seed": seed,
        "effective_start_inclusive": stamp(START), "effective_cutoff_exclusive": stamp(END),
        "recorded_cutoff_inclusive": stamp(END), "late_fee_replay_recorded_cutoff_inclusive": stamp(END + 3 * DAY),
        "canonical_customer_count": CUSTOMERS, "product_accounts": account_counts,
        "customer_account_mix": {"zero": accounts_per_customer.count(0), "one": accounts_per_customer.count(1),
                                 "multiple": sum(n > 1 for n in accounts_per_customer)},
        "assumptions": ASSUMPTIONS, "files": files,
        "data_quality": {"status": "NOT_RUN", "instructions": "See src/verify_synthetic_sources.py."},
    }
    (output / "manifest_v1.0.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "data/synthetic_sources")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    generate(args.output, args.seed)
