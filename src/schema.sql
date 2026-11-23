-- MIS 636 Assignment 2 | Physical schema for contract v1.0
-- Execute against an empty DuckDB database.
-- Temporal validity, identity resolution, activity-code eligibility, deduplication,
-- adjustment limits, maturity, scenario parity and reconciliations are ELT checks.
-- See docs/02_source_target_mapping.md for the enforcement boundaries.

-- Campaign catalog
CREATE TABLE campaign (
    campaign_id VARCHAR NOT NULL,
    channel VARCHAR NOT NULL CHECK (channel IN ('GOOGLE_ADS', 'META_ADS', 'PAID_AFFILIATES')),
    active_from DATE NOT NULL,
    active_through DATE,
    PRIMARY KEY (campaign_id),
    CHECK (active_through >= active_from)
);

-- Planned and actual daily spend
CREATE TABLE campaign_day (
    campaign_id VARCHAR NOT NULL REFERENCES campaign(campaign_id),
    spend_date DATE NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    actual_cents BIGINT NOT NULL,
    eligible_cents BIGINT NOT NULL,
    planned_cents BIGINT,
    PRIMARY KEY (campaign_id, spend_date, recorded_at),
    CHECK (eligible_cents BETWEEN 0 AND actual_cents),
    CHECK (planned_cents >= 0)
);

-- Period cap and targets
CREATE TABLE campaign_budget (
    campaign_id VARCHAR NOT NULL REFERENCES campaign(campaign_id),
    period_start DATE NOT NULL,
    period_kind VARCHAR NOT NULL CHECK (period_kind IN ('WEEK', 'MONTH')),
    recorded_at TIMESTAMPTZ NOT NULL,
    period_end_exclusive DATE NOT NULL,
    budget_cents BIGINT,
    target_cac_cents BIGINT,
    target_activation DECIMAL(12,8),
    PRIMARY KEY (campaign_id, period_start, period_kind, recorded_at),
    CHECK (period_end_exclusive > period_start),
    CHECK (budget_cents >= 0),
    CHECK (target_cac_cents >= 0),
    CHECK (target_activation BETWEEN 0 AND 1)
);

-- Signup observations
CREATE TABLE registration (
    registration_id VARCHAR NOT NULL,
    registration_identity VARCHAR NOT NULL,
    visitor_identity VARCHAR,
    registration_at TIMESTAMPTZ NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    state VARCHAR NOT NULL CHECK (state IN ('VALID', 'VOID')),
    PRIMARY KEY (registration_id)
);

-- Identity evidence
CREATE TABLE identity_link (
    identity_link_id VARCHAR NOT NULL,
    identity_key VARCHAR NOT NULL,
    canonical_customer_id VARCHAR,
    effective_from TIMESTAMPTZ NOT NULL,
    effective_to TIMESTAMPTZ,
    recorded_at TIMESTAMPTZ NOT NULL,
    link_state VARCHAR NOT NULL CHECK (link_state IN ('CANDIDATE', 'RETRACTED')),
    PRIMARY KEY (identity_link_id),
    CHECK (effective_to > effective_from),
    CHECK (link_state <> 'CANDIDATE' OR canonical_customer_id IS NOT NULL)
);

-- Tracked marketing evidence
CREATE TABLE marketing_touch (
    touch_id VARCHAR NOT NULL,
    visitor_identity VARCHAR NOT NULL,
    campaign_id VARCHAR NOT NULL REFERENCES campaign(campaign_id),
    touched_at TIMESTAMPTZ NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    state VARCHAR NOT NULL CHECK (state IN ('ELIGIBLE', 'VOID')),
    PRIMARY KEY (touch_id)
);

-- Raw acquisition intent
CREATE TABLE registration_feature (
    feature_id VARCHAR NOT NULL,
    registration_id VARCHAR NOT NULL REFERENCES registration(registration_id),
    intent VARCHAR,
    effective_at TIMESTAMPTZ NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (feature_id)
);

-- Ownership
CREATE TABLE product_account (
    account_id VARCHAR NOT NULL,
    owner_identity VARCHAR NOT NULL,
    product VARCHAR NOT NULL CHECK (product IN ('SAVINGS', 'DEBIT', 'CREDIT', 'PERSONAL', 'MORTGAGE')),
    opened_at TIMESTAMPTZ NOT NULL,
    closed_at TIMESTAMPTZ,
    recorded_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (account_id),
    CHECK (closed_at >= opened_at)
);

-- Immutable ingestion rows
CREATE TABLE product_activity_delivery (
    delivery_id VARCHAR NOT NULL,
    source_key VARCHAR NOT NULL,
    account_id VARCHAR NOT NULL REFERENCES product_account(account_id),
    activity_code VARCHAR NOT NULL,
    effective_at TIMESTAMPTZ NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    state VARCHAR NOT NULL CHECK (state IN ('SETTLED', 'POSTED', 'CONFIRMED', 'PENDING', 'VOID')),
    amount_cents BIGINT,
    annual_rate DECIMAL(12,8),
    balance_kind VARCHAR,
    original_source_key VARCHAR,
    adjustment_kind VARCHAR CHECK (adjustment_kind IN ('RESTATEMENT_REDUCTION', 'LATER_REDUCTION', 'RECOVERY')),
    component VARCHAR,
    PRIMARY KEY (delivery_id),
    CHECK (amount_cents >= 0)
);

-- Reproducible snapshot
CREATE TABLE run_manifest (
    run_id VARCHAR NOT NULL,
    effective_cutoff TIMESTAMPTZ NOT NULL,
    recorded_cutoff TIMESTAMPTZ NOT NULL,
    source_manifest_hash VARCHAR NOT NULL,
    contract_version VARCHAR NOT NULL,
    build_version VARCHAR NOT NULL,
    PRIMARY KEY (run_id)
);

-- Inspectable rejects
CREATE TABLE exception_log (
    run_id VARCHAR NOT NULL REFERENCES run_manifest(run_id),
    source_table VARCHAR NOT NULL,
    source_id VARCHAR NOT NULL,
    reason VARCHAR NOT NULL CHECK (reason IN ('DUPLICATE_DELIVERY', 'CONFLICTING_SOURCE_KEY', 'IDENTITY_MISSING', 'IDENTITY_AMBIGUOUS', 'INVALID_REFERENCE', 'INVALID_STATE', 'INVALID_CODE', 'INVALID_ADJUSTMENT', 'OVER_REVERSAL', 'LATE_RECORD', 'MISSING_PLAN')),
    detected_at TIMESTAMPTZ NOT NULL,
    detail JSON NOT NULL,
    PRIMARY KEY (run_id, source_table, source_id, reason)
);

-- Canonical registration
CREATE TABLE acquisition (
    customer_id VARCHAR NOT NULL,
    registration_id VARCHAR NOT NULL UNIQUE REFERENCES registration(registration_id),
    registration_at TIMESTAMPTZ NOT NULL,
    signup_date DATE NOT NULL,
    signup_month DATE NOT NULL,
    PRIMARY KEY (customer_id)
);

-- Immutable marketing selection
CREATE TABLE attribution (
    customer_id VARCHAR NOT NULL REFERENCES acquisition(customer_id),
    touch_id VARCHAR REFERENCES marketing_touch(touch_id),
    campaign_id VARCHAR REFERENCES campaign(campaign_id),
    channel VARCHAR NOT NULL CHECK (channel IN ('GOOGLE_ADS', 'META_ADS', 'PAID_AFFILIATES', 'UNKNOWN')),
    status VARCHAR NOT NULL CHECK (status IN ('MATCHED', 'NO_ELIGIBLE_TOUCH', 'MISSING_VISITOR_LINK', 'AMBIGUOUS_VISITOR_LINK')),
    rule_version VARCHAR NOT NULL,
    feature_cutoff TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (customer_id),
    CHECK ((status = 'MATCHED' AND touch_id IS NOT NULL AND campaign_id IS NOT NULL AND channel <> 'UNKNOWN') OR (status <> 'MATCHED' AND touch_id IS NULL AND campaign_id IS NULL AND channel = 'UNKNOWN'))
);

-- Deduplicated activity and ownership
CREATE TABLE canonical_activity (
    run_id VARCHAR NOT NULL REFERENCES run_manifest(run_id),
    source_key VARCHAR NOT NULL,
    delivery_id VARCHAR NOT NULL REFERENCES product_activity_delivery(delivery_id),
    account_id VARCHAR NOT NULL REFERENCES product_account(account_id),
    customer_id VARCHAR REFERENCES acquisition(customer_id),
    status VARCHAR NOT NULL CHECK (status IN ('ACCEPTED', 'OWNER_UNRESOLVED')),
    PRIMARY KEY (run_id, source_key),
    CHECK ((status = 'ACCEPTED') = (customer_id IS NOT NULL))
);

-- Signed ledger
CREATE TABLE financial_event (
    run_id VARCHAR NOT NULL REFERENCES run_manifest(run_id),
    event_id VARCHAR NOT NULL,
    source_key VARCHAR NOT NULL,
    component VARCHAR NOT NULL,
    account_id VARCHAR NOT NULL REFERENCES product_account(account_id),
    customer_id VARCHAR NOT NULL REFERENCES acquisition(customer_id),
    event_code VARCHAR NOT NULL,
    class VARCHAR NOT NULL CHECK (class IN ('REVENUE', 'COST')),
    signed_cents BIGINT NOT NULL,
    effective_at TIMESTAMPTZ NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL,
    original_event_id VARCHAR,
    adjustment_kind VARCHAR CHECK (adjustment_kind IN ('RESTATEMENT_REDUCTION', 'LATER_REDUCTION', 'RECOVERY')),
    PRIMARY KEY (run_id, event_id),
    FOREIGN KEY (run_id, source_key) REFERENCES canonical_activity (run_id, source_key),
    FOREIGN KEY (run_id, original_event_id) REFERENCES financial_event (run_id, event_id),
    CHECK ((original_event_id IS NULL AND adjustment_kind IS NULL AND signed_cents >= 0) OR (original_event_id IS NOT NULL AND adjustment_kind IS NOT NULL AND signed_cents <= 0)),
    UNIQUE (run_id, source_key, component)
);

-- First qualifying action
CREATE TABLE activation (
    run_id VARCHAR NOT NULL REFERENCES run_manifest(run_id),
    customer_id VARCHAR NOT NULL REFERENCES acquisition(customer_id),
    product VARCHAR NOT NULL CHECK (product IN ('SAVINGS', 'DEBIT', 'CREDIT', 'PERSONAL', 'MORTGAGE')),
    activation_at TIMESTAMPTZ,
    source_key VARCHAR,
    status VARCHAR NOT NULL CHECK (status IN ('QUALIFIED', 'NO_QUALIFYING_EVENT', 'PENDING')),
    PRIMARY KEY (run_id, customer_id, product),
    FOREIGN KEY (run_id, source_key) REFERENCES canonical_activity (run_id, source_key),
    CHECK ((status = 'QUALIFIED' AND activation_at IS NOT NULL AND source_key IS NOT NULL) OR (status <> 'QUALIFIED' AND activation_at IS NULL AND source_key IS NULL))
);

-- Frozen acquisition inputs
CREATE TABLE feature_snapshot (
    customer_id VARCHAR NOT NULL REFERENCES acquisition(customer_id),
    feature_cutoff TIMESTAMPTZ NOT NULL,
    channel VARCHAR NOT NULL CHECK (channel IN ('GOOGLE_ADS', 'META_ADS', 'PAID_AFFILIATES', 'UNKNOWN')),
    normalized_intent VARCHAR NOT NULL CHECK (normalized_intent IN ('EVERYDAY', 'BORROW', 'UNKNOWN')),
    feature_id VARCHAR REFERENCES registration_feature(feature_id),
    feature_available_at TIMESTAMPTZ,
    input_status VARCHAR NOT NULL CHECK (input_status IN ('VALID', 'MISSING', 'INVALID', 'LATE')),
    snapshot_hash VARCHAR NOT NULL,
    PRIMARY KEY (customer_id),
    CHECK ((feature_id IS NULL) = (feature_available_at IS NULL)),
    CHECK (feature_available_at <= feature_cutoff)
);

-- Immutable parameters
CREATE TABLE forecast_model (
    model_version VARCHAR NOT NULL,
    scenario VARCHAR NOT NULL CHECK (scenario IN ('BASELINE', 'EQUAL_CHANNEL')),
    parameter_hash VARCHAR NOT NULL UNIQUE,
    parameter_payload JSON NOT NULL,
    parent_version VARCHAR REFERENCES forecast_model(model_version),
    PRIMARY KEY (model_version),
    CHECK ((scenario = 'BASELINE' AND parent_version IS NULL) OR (scenario = 'EQUAL_CHANNEL' AND parent_version IS NOT NULL))
);

-- Fixed score or later sensitivity
CREATE TABLE prediction (
    customer_id VARCHAR NOT NULL REFERENCES feature_snapshot(customer_id),
    model_version VARCHAR NOT NULL REFERENCES forecast_model(model_version),
    scored_at TIMESTAMPTZ NOT NULL,
    written_at TIMESTAMPTZ NOT NULL,
    expected_365_cents BIGINT NOT NULL,
    PRIMARY KEY (customer_id, model_version)
);

-- Trajectory
CREATE TABLE prediction_age (
    customer_id VARCHAR NOT NULL,
    model_version VARCHAR NOT NULL,
    age_days INTEGER NOT NULL CHECK (age_days IN (30, 90, 180, 365)),
    expected_cents BIGINT NOT NULL,
    PRIMARY KEY (customer_id, model_version, age_days),
    FOREIGN KEY (customer_id, model_version) REFERENCES prediction (customer_id, model_version)
);

-- Audited allocation components
CREATE TABLE spend_allocation (
    run_id VARCHAR NOT NULL REFERENCES run_manifest(run_id),
    campaign_id VARCHAR NOT NULL REFERENCES campaign(campaign_id),
    spend_date DATE NOT NULL,
    allocation_method VARCHAR NOT NULL CHECK (allocation_method IN ('CALENDAR', 'TOUCH_WEIGHT')),
    signup_month DATE NOT NULL,
    spend_recorded_at TIMESTAMPTZ NOT NULL,
    allocated_cents BIGINT NOT NULL,
    winner_count INTEGER,
    lag_incomplete BOOLEAN NOT NULL,
    PRIMARY KEY (run_id, campaign_id, spend_date, allocation_method, signup_month),
    FOREIGN KEY (campaign_id, spend_date, spend_recorded_at) REFERENCES campaign_day (campaign_id, spend_date, recorded_at),
    CHECK (allocated_cents >= 0),
    CHECK ((allocation_method = 'CALENDAR' AND winner_count IS NULL
        AND signup_month = CAST(date_trunc('month', spend_date) AS DATE))
        OR (allocation_method = 'TOUCH_WEIGHT' AND winner_count IS NOT NULL AND winner_count >= 0))
);

-- Realized customer outcome
CREATE TABLE customer_age (
    run_id VARCHAR NOT NULL REFERENCES run_manifest(run_id),
    customer_id VARCHAR NOT NULL REFERENCES acquisition(customer_id),
    age_days INTEGER NOT NULL CHECK (age_days IN (30, 90, 180, 365)),
    horizon_end TIMESTAMPTZ NOT NULL,
    maturity VARCHAR NOT NULL CHECK (maturity IN ('MATURE', 'PENDING')),
    revenue_cents BIGINT,
    cost_cents BIGINT,
    contribution_cents BIGINT,
    PRIMARY KEY (run_id, customer_id, age_days),
    CHECK ((maturity = 'MATURE' AND revenue_cents IS NOT NULL AND cost_cents IS NOT NULL AND contribution_cents IS NOT NULL AND contribution_cents = revenue_cents - cost_cents) OR (maturity = 'PENDING' AND revenue_cents IS NULL AND cost_cents IS NULL AND contribution_cents IS NULL))
);

-- Period and age reporting
CREATE TABLE channel_cohort (
    run_id VARCHAR NOT NULL REFERENCES run_manifest(run_id),
    channel VARCHAR NOT NULL CHECK (channel IN ('GOOGLE_ADS', 'META_ADS', 'PAID_AFFILIATES', 'UNKNOWN')),
    signup_month DATE NOT NULL,
    age_days INTEGER NOT NULL CHECK (age_days IN (30, 90, 180, 365)),
    allocation_method VARCHAR NOT NULL CHECK (allocation_method IN ('CALENDAR', 'TOUCH_WEIGHT')),
    model_version VARCHAR NOT NULL REFERENCES forecast_model(model_version),
    cohort_status VARCHAR NOT NULL CHECK (cohort_status IN ('MATURE', 'PENDING', 'SPEND_ONLY')),
    registrations INTEGER NOT NULL,
    mature_customers INTEGER NOT NULL,
    paid_attributed_customers INTEGER NOT NULL,
    eligible_spend_cents BIGINT,
    revenue_cents BIGINT,
    cost_cents BIGINT,
    contribution_cents BIGINT,
    expected_comparable_cents BIGINT,
    expected_all_cents BIGINT,
    cac_usd DECIMAL(28,8),
    revenue_per_customer_usd DECIMAL(28,8),
    revenue_roas DECIMAL(28,8),
    predicted_ltv_cac DECIMAL(28,8),
    realized_per_spend DECIMAL(28,8),
    after_spend_cents BIGINT,
    paid_metric_status VARCHAR NOT NULL CHECK (paid_metric_status IN ('AVAILABLE', 'ZERO_DENOMINATOR', 'UNKNOWN_CHANNEL', 'SPEND_MISSING', 'PENDING')),
    PRIMARY KEY (run_id, channel, signup_month, age_days, allocation_method, model_version),
    CHECK (mature_customers BETWEEN 0 AND registrations),
    CHECK (paid_attributed_customers BETWEEN 0 AND registrations),
    CHECK (eligible_spend_cents >= 0),
    CHECK (cohort_status <> 'SPEND_ONLY' OR (registrations = 0 AND eligible_spend_cents IS NOT NULL
        AND cac_usd IS NULL AND revenue_roas IS NULL AND paid_metric_status = 'ZERO_DENOMINATOR'))
);

-- Operational campaign output
CREATE TABLE campaign_performance_day (
    run_id VARCHAR NOT NULL REFERENCES run_manifest(run_id),
    campaign_id VARCHAR NOT NULL REFERENCES campaign(campaign_id),
    report_date DATE NOT NULL,
    actual_cents BIGINT,
    eligible_spend_cents BIGINT,
    planned_cents BIGINT,
    registrations INTEGER NOT NULL,
    mature_30_customers INTEGER NOT NULL,
    activated_30_customers INTEGER NOT NULL,
    baseline_forecast_total_cents BIGINT NOT NULL,
    cac_usd DECIMAL(28,8),
    actual_to_date_cents BIGINT,
    plan_to_date_cents BIGINT,
    remaining_budget_cents BIGINT,
    pace_ratio DECIMAL(28,8),
    activation_rate DECIMAL(28,8),
    data_status VARCHAR NOT NULL CHECK (data_status IN ('READY', 'MISSING_PLAN', 'MISSING_SPEND', 'INCOMPLETE')),
    pacing_status VARCHAR NOT NULL CHECK (pacing_status IN ('FLAG', 'OK', 'UNAVAILABLE')),
    PRIMARY KEY (run_id, campaign_id, report_date),
    CHECK (mature_30_customers BETWEEN 0 AND registrations),
    CHECK (activated_30_customers BETWEEN 0 AND mature_30_customers),
    CHECK (plan_to_date_cents IS NOT NULL OR (pace_ratio IS NULL AND pacing_status = 'UNAVAILABLE')),
    CHECK (eligible_spend_cents BETWEEN 0 AND actual_cents),
    CHECK (planned_cents >= 0)
);
