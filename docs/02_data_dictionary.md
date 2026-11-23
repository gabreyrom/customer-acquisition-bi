# Field-level data dictionary

Companion to [the v1.0 data contract](02_data_contract.md) and [source-to-target mapping](02_source_target_mapping.md). BIGINT monetary columns ending in cents store exact USD cents. *_usd columns use decimal USD, and other ratio columns are decimal fractions or multiples. TS columns use TIMESTAMPTZ and are interpreted in UTC. The contract remains authoritative for financial rules.

## campaign
Campaign catalog. One row per campaign_id.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| campaign_id | VARCHAR | Yes | PK | Campaign identifier. Input: campaign.campaign_id. |
| channel | VARCHAR | Yes | — | Paid acquisition category or UNKNOWN for unresolved attribution. Input: campaign.channel. Values: GOOGLE_ADS, META_ADS, PAID_AFFILIATES. |
| active_from | DATE | Yes | — | First eligible campaign date. Input: campaign.active_from. |
| active_through | DATE | No | — | Last eligible campaign date. Input: campaign.active_through. |

## campaign_day
Planned and actual daily spend. One row per campaign_id, spend_date, recorded_at.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| campaign_id | VARCHAR | Yes | PK; FK campaign.campaign_id | Campaign identifier. Input: campaign_day.campaign_id. |
| spend_date | DATE | Yes | PK | UTC date to which source campaign spend belongs. Input: campaign_day.spend_date. |
| recorded_at | TIMESTAMPTZ | Yes | PK | Inclusive availability instant from the source or inherited component. Input: campaign_day.recorded_at. |
| actual_cents | BIGINT | Yes | — | Actual campaign spend for the source or report day. Input: campaign_day.actual_cents. |
| eligible_cents | BIGINT | Yes | — | Portion of actual spend eligible for acquisition metrics. Input: campaign_day.eligible_cents. |
| planned_cents | BIGINT | No | — | Planned spend for the source or report day. Input: campaign_day.planned_cents. |

## campaign_budget
Period cap and targets. One row per campaign_id, period_start, period_kind, recorded_at.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| campaign_id | VARCHAR | Yes | PK; FK campaign.campaign_id | Campaign identifier. Input: campaign_budget.campaign_id. |
| period_start | DATE | Yes | PK | Inclusive UTC start of the budget period. Input: campaign_budget.period_start. |
| period_kind | VARCHAR | Yes | PK | Budget interval category. Input: campaign_budget.period_kind. Values: WEEK, MONTH. |
| recorded_at | TIMESTAMPTZ | Yes | PK | Inclusive availability instant from the source or inherited component. Input: campaign_budget.recorded_at. |
| period_end_exclusive | DATE | Yes | — | First date outside the budget interval. Input: campaign_budget.period_end_exclusive. |
| budget_cents | BIGINT | No | — | Approved cap for the budget period. Input: campaign_budget.budget_cents. |
| target_cac_cents | BIGINT | No | — | Acquisition cost target per signup. Input: campaign_budget.target_cac_cents. |
| target_activation | DECIMAL(12,8) | No | — | Target fraction of mature signups activated. Input: campaign_budget.target_activation. |

## registration
Signup observations. One row per registration_id.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| registration_id | VARCHAR | Yes | PK | Signup observation identifier. Input: registration.registration_id. |
| registration_identity | VARCHAR | Yes | — | Namespaced source signup identity. Input: registration.registration_identity. |
| visitor_identity | VARCHAR | No | — | Namespaced tracking identity from signup or touch. Input: registration.visitor_identity. |
| registration_at | TIMESTAMPTZ | Yes | — | Actual signup instant used as the acquisition clock. Input: registration.registration_at. |
| recorded_at | TIMESTAMPTZ | Yes | — | Inclusive availability instant from the source or inherited component. Input: registration.recorded_at. |
| state | VARCHAR | Yes | — | Lifecycle state supplied by the source relation. Input: registration.state. Values: VALID, VOID. |

## identity_link
Identity evidence. One row per identity_link_id.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| identity_link_id | VARCHAR | Yes | PK | Identity evidence row identifier. Input: identity_link.identity_link_id. |
| identity_key | VARCHAR | Yes | — | Namespaced source identifier represented by this claim. Input: identity_link.identity_key. |
| canonical_customer_id | VARCHAR | No | — | Candidate synthetic customer identifier for the claim. Input: identity_link.canonical_customer_id. |
| effective_from | TIMESTAMPTZ | Yes | — | Inclusive start of the identity claim. Input: identity_link.effective_from. |
| effective_to | TIMESTAMPTZ | No | — | Exclusive end of the identity claim. Input: identity_link.effective_to. |
| recorded_at | TIMESTAMPTZ | Yes | — | Inclusive availability instant from the source or inherited component. Input: identity_link.recorded_at. |
| link_state | VARCHAR | Yes | — | Whether the source asserts or retracts the claim. Input: identity_link.link_state. Values: CANDIDATE, RETRACTED. |

## marketing_touch
Tracked marketing evidence. One row per touch_id.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| touch_id | VARCHAR | Yes | PK | Tracked touch identifier. Input: marketing_touch.touch_id. |
| visitor_identity | VARCHAR | Yes | — | Namespaced tracking identity from signup or touch. Input: marketing_touch.visitor_identity. |
| campaign_id | VARCHAR | Yes | FK campaign.campaign_id | Campaign identifier. Input: marketing_touch.campaign_id. |
| touched_at | TIMESTAMPTZ | Yes | — | Instant the marketing touch occurred. Input: marketing_touch.touched_at. |
| recorded_at | TIMESTAMPTZ | Yes | — | Inclusive availability instant from the source or inherited component. Input: marketing_touch.recorded_at. |
| state | VARCHAR | Yes | — | Lifecycle state supplied by the source relation. Input: marketing_touch.state. Values: ELIGIBLE, VOID. |

## registration_feature
Raw acquisition intent. One row per feature_id.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| feature_id | VARCHAR | Yes | PK | Signup feature observation identifier. Input: registration_feature.feature_id. |
| registration_id | VARCHAR | Yes | FK registration.registration_id | Signup observation identifier. Input: registration_feature.registration_id. |
| intent | VARCHAR | No | — | Raw signup intent observation. Input: registration_feature.intent. |
| effective_at | TIMESTAMPTZ | Yes | — | Business instant for the source observation or canonical event. Input: registration_feature.effective_at. |
| recorded_at | TIMESTAMPTZ | Yes | — | Inclusive availability instant from the source or inherited component. Input: registration_feature.recorded_at. |

## product_account
Ownership. One row per account_id.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| account_id | VARCHAR | Yes | PK | Product account identifier. Input: product_account.account_id. |
| owner_identity | VARCHAR | Yes | — | Namespaced identity used to resolve account owner. Input: product_account.owner_identity. |
| product | VARCHAR | Yes | — | One of the five product families. Input: product_account.product. Values: SAVINGS, DEBIT, CREDIT, PERSONAL, MORTGAGE. |
| opened_at | TIMESTAMPTZ | Yes | — | Account opening instant. Input: product_account.opened_at. |
| closed_at | TIMESTAMPTZ | No | — | Account closing instant. Input: product_account.closed_at. |
| recorded_at | TIMESTAMPTZ | Yes | — | Inclusive availability instant from the source or inherited component. Input: product_account.recorded_at. |

## product_activity_delivery
Immutable ingestion rows. One row per delivery_id.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| delivery_id | VARCHAR | Yes | PK | Physical ingestion row identifier. Input: product_activity_delivery.delivery_id. |
| source_key | VARCHAR | Yes | — | Stable namespaced business record identifier, reusable across deliveries. Input: product_activity_delivery.source_key. |
| account_id | VARCHAR | Yes | FK product_account.account_id | Product account identifier. Input: product_activity_delivery.account_id. |
| activity_code | VARCHAR | Yes | — | Source activity classification selecting the mapping rule. Input: product_activity_delivery.activity_code. |
| effective_at | TIMESTAMPTZ | Yes | — | Business instant for the source observation or canonical event. Input: product_activity_delivery.effective_at. |
| recorded_at | TIMESTAMPTZ | Yes | — | Inclusive availability instant from the source or inherited component. Input: product_activity_delivery.recorded_at. |
| state | VARCHAR | Yes | — | Lifecycle state supplied by the source relation. Input: product_activity_delivery.state. Values: SETTLED, POSTED, CONFIRMED, PENDING, VOID. |
| amount_cents | BIGINT | No | — | Raw move, component or balance basis as specified by activity code. Input: product_activity_delivery.amount_cents. |
| annual_rate | DECIMAL(12,8) | No | — | Annual accrual rate as a decimal fraction. Input: product_activity_delivery.annual_rate. |
| balance_kind | VARCHAR | No | — | Balance basis for a daily accrual component. Input: product_activity_delivery.balance_kind. |
| original_source_key | VARCHAR | No | — | Source pointer for operational linkage or an adjustment target. Input: product_activity_delivery.original_source_key. |
| adjustment_kind | VARCHAR | No | — | Recognition timing and adjustment category. Input: product_activity_delivery.adjustment_kind. Values: RESTATEMENT_REDUCTION, LATER_REDUCTION, RECOVERY. |
| component | VARCHAR | No | — | Component discriminator or source adjustment target code. Input: product_activity_delivery.component. |

## run_manifest
Reproducible snapshot. One row per run_id.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| run_id | VARCHAR | Yes | PK | Immutable report snapshot identifier. Referenced input or derived key. |
| effective_cutoff | TIMESTAMPTZ | Yes | — | Exclusive run boundary for effective data completeness. Derived per mapping. |
| recorded_cutoff | TIMESTAMPTZ | Yes | — | Inclusive source availability boundary for the run. Derived per mapping. |
| source_manifest_hash | VARCHAR | Yes | — | Digest of the input extract manifest. Derived per mapping. |
| contract_version | VARCHAR | Yes | — | Data contract version used for the run. Derived per mapping. |
| build_version | VARCHAR | Yes | — | Transformation build identifier. Derived per mapping. |

## exception_log
Inspectable rejects. One row per run_id, source_table, source_id, reason.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| run_id | VARCHAR | Yes | PK; FK run_manifest.run_id | Immutable report snapshot identifier. Referenced input or derived key. |
| source_table | VARCHAR | Yes | PK | Name of the source relation associated with an exception. Referenced input or derived key. |
| source_id | VARCHAR | Yes | PK | Identifier of the affected input record. Referenced input or derived key. |
| reason | VARCHAR | Yes | PK | Machine-readable exception category. Referenced input or derived key. Values: DUPLICATE_DELIVERY, CONFLICTING_SOURCE_KEY, IDENTITY_MISSING, IDENTITY_AMBIGUOUS, INVALID_REFERENCE, INVALID_STATE, INVALID_CODE, INVALID_ADJUSTMENT, OVER_REVERSAL, LATE_RECORD, MISSING_PLAN. |
| detected_at | TIMESTAMPTZ | Yes | — | Instant the exception was recorded. Derived per mapping. |
| detail | JSON | Yes | — | Structured diagnostic and provenance values. Derived per mapping. |

## acquisition
Canonical registration. One row per customer_id.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| customer_id | VARCHAR | Yes | PK | Canonical acquired customer identifier. Referenced input or derived key. |
| registration_id | VARCHAR | Yes | unique; FK registration.registration_id | Signup observation identifier. Referenced input or derived key. |
| registration_at | TIMESTAMPTZ | Yes | — | Actual signup instant used as the acquisition clock. Derived per mapping. |
| signup_date | DATE | Yes | — | UTC date derived from registration instant. Derived per mapping. |
| signup_month | DATE | Yes | — | First UTC calendar date of the allocated or acquisition month. Derived per mapping. |

## attribution
Immutable marketing selection. One row per customer_id.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| customer_id | VARCHAR | Yes | PK; FK acquisition.customer_id | Canonical acquired customer identifier. Referenced input or derived key. |
| touch_id | VARCHAR | No | FK marketing_touch.touch_id | Tracked touch identifier. Referenced input or derived key. |
| campaign_id | VARCHAR | No | FK campaign.campaign_id | Campaign identifier. Referenced input or derived key. |
| channel | VARCHAR | Yes | — | Paid acquisition category or UNKNOWN for unresolved attribution. Derived per mapping. Values: GOOGLE_ADS, META_ADS, PAID_AFFILIATES, UNKNOWN. |
| status | VARCHAR | Yes | — | Resolution or lifecycle outcome defined for this relation. Derived per mapping. Values: MATCHED, NO_ELIGIBLE_TOUCH, MISSING_VISITOR_LINK, AMBIGUOUS_VISITOR_LINK. |
| rule_version | VARCHAR | Yes | — | Version of immutable touch-selection policy. Derived per mapping. |
| feature_cutoff | TIMESTAMPTZ | Yes | — | Acquisition instant used as point-in-time input boundary. Derived per mapping. |

## canonical_activity
Deduplicated activity and ownership. One row per run_id, source_key.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| run_id | VARCHAR | Yes | PK; FK run_manifest.run_id | Immutable report snapshot identifier. Referenced input or derived key. |
| source_key | VARCHAR | Yes | PK | Stable namespaced business record identifier, reusable across deliveries. Referenced input or derived key. |
| delivery_id | VARCHAR | Yes | FK product_activity_delivery.delivery_id | Physical ingestion row identifier. Referenced input or derived key. |
| account_id | VARCHAR | Yes | FK product_account.account_id | Product account identifier. Referenced input or derived key. |
| customer_id | VARCHAR | No | FK acquisition.customer_id | Canonical acquired customer identifier. Referenced input or derived key. |
| status | VARCHAR | Yes | — | Resolution or lifecycle outcome defined for this relation. Derived per mapping. Values: ACCEPTED, OWNER_UNRESOLVED. |

## financial_event
Signed ledger. One row per run_id, event_id.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| run_id | VARCHAR | Yes | PK; FK run_manifest.run_id; FK (run_id, source_key) → canonical_activity (run_id, source_key); FK (run_id, original_event_id) → financial_event (run_id, event_id) | Immutable report snapshot identifier. Referenced input or derived key. |
| event_id | VARCHAR | Yes | PK | Stable canonical component identifier. Referenced input or derived key. |
| source_key | VARCHAR | Yes | FK (run_id, source_key) → canonical_activity (run_id, source_key) | Stable namespaced business record identifier, reusable across deliveries. Referenced input or derived key. |
| component | VARCHAR | Yes | — | Component discriminator or source adjustment target code. Derived per mapping. |
| account_id | VARCHAR | Yes | FK product_account.account_id | Product account identifier. Referenced input or derived key. |
| customer_id | VARCHAR | Yes | FK acquisition.customer_id | Canonical acquired customer identifier. Referenced input or derived key. |
| event_code | VARCHAR | Yes | — | Workstream A code defining economic treatment. Derived per mapping. |
| class | VARCHAR | Yes | — | Revenue or cost bucket for a signed component. Derived per mapping. Values: REVENUE, COST. |
| signed_cents | BIGINT | Yes | — | Signed amount within its revenue or cost class. Derived per mapping. |
| effective_at | TIMESTAMPTZ | Yes | — | Business instant for the source observation or canonical event. Derived per mapping. |
| recorded_at | TIMESTAMPTZ | Yes | — | Inclusive availability instant from the source or inherited component. Derived per mapping. |
| original_event_id | VARCHAR | No | FK (run_id, original_event_id) → financial_event (run_id, event_id) | Canonical event targeted by the adjustment. Referenced input or derived key. |
| adjustment_kind | VARCHAR | No | — | Recognition timing and adjustment category. Derived per mapping. Values: RESTATEMENT_REDUCTION, LATER_REDUCTION, RECOVERY. |

## activation
First qualifying action. One row per run_id, customer_id, product.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| run_id | VARCHAR | Yes | PK; FK run_manifest.run_id; FK (run_id, source_key) → canonical_activity (run_id, source_key) | Immutable report snapshot identifier. Referenced input or derived key. |
| customer_id | VARCHAR | Yes | PK; FK acquisition.customer_id | Canonical acquired customer identifier. Referenced input or derived key. |
| product | VARCHAR | Yes | PK | One of the five product families. Referenced input or derived key. Values: SAVINGS, DEBIT, CREDIT, PERSONAL, MORTGAGE. |
| activation_at | TIMESTAMPTZ | No | — | First qualifying event instant for this customer and product. Derived per mapping. |
| source_key | VARCHAR | No | FK (run_id, source_key) → canonical_activity (run_id, source_key) | Stable namespaced business record identifier, reusable across deliveries. Referenced input or derived key. |
| status | VARCHAR | Yes | — | Resolution or lifecycle outcome defined for this relation. Derived per mapping. Values: QUALIFIED, NO_QUALIFYING_EVENT, PENDING. |

## feature_snapshot
Frozen acquisition inputs. One row per customer_id.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| customer_id | VARCHAR | Yes | PK; FK acquisition.customer_id | Canonical acquired customer identifier. Referenced input or derived key. |
| feature_cutoff | TIMESTAMPTZ | Yes | — | Acquisition instant used as point-in-time input boundary. Derived per mapping. |
| channel | VARCHAR | Yes | — | Paid acquisition category or UNKNOWN for unresolved attribution. Derived per mapping. Values: GOOGLE_ADS, META_ADS, PAID_AFFILIATES, UNKNOWN. |
| normalized_intent | VARCHAR | Yes | — | Eligible signup intent category after fallback. Derived per mapping. Values: EVERYDAY, BORROW, UNKNOWN. |
| feature_id | VARCHAR | No | FK registration_feature.feature_id | Signup feature observation identifier. Referenced input or derived key. |
| feature_available_at | TIMESTAMPTZ | No | — | Recorded availability of the retained feature. Derived per mapping. |
| input_status | VARCHAR | Yes | — | Availability or validity outcome of the feature input. Derived per mapping. Values: VALID, MISSING, INVALID, LATE. |
| snapshot_hash | VARCHAR | Yes | — | Digest of the frozen feature values and provenance. Derived per mapping. |

## forecast_model
Immutable parameters. One row per model_version.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| model_version | VARCHAR | Yes | PK | Immutable forecast parameter version. Referenced input or derived key. |
| scenario | VARCHAR | Yes | — | Baseline or equal-channel forecast purpose. Derived per mapping. Values: BASELINE, EQUAL_CHANNEL. |
| parameter_hash | VARCHAR | Yes | unique | Digest of the immutable model parameter payload. Referenced input or derived key. |
| parameter_payload | JSON | Yes | — | Scenario multipliers, contribution weights and trajectory factors. Derived per mapping. |
| parent_version | VARCHAR | No | FK forecast_model.model_version | Baseline version reused by the sensitivity. Referenced input or derived key. |

## prediction
Fixed score or later sensitivity. One row per customer_id, model_version.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| customer_id | VARCHAR | Yes | PK; FK feature_snapshot.customer_id | Canonical acquired customer identifier. Referenced input or derived key. |
| model_version | VARCHAR | Yes | PK; FK forecast_model.model_version | Immutable forecast parameter version. Referenced input or derived key. |
| scored_at | TIMESTAMPTZ | Yes | — | Time the frozen or sensitivity score was calculated. Derived per mapping. |
| written_at | TIMESTAMPTZ | Yes | — | Time the score was persisted. Derived per mapping. |
| expected_365_cents | BIGINT | Yes | — | Frozen expected first-year contribution under this model version. Derived per mapping. |

## prediction_age
Trajectory. One row per customer_id, model_version, age_days.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| customer_id | VARCHAR | Yes | PK; FK (customer_id, model_version) → prediction (customer_id, model_version) | Canonical acquired customer identifier. Referenced input or derived key. |
| model_version | VARCHAR | Yes | PK; FK (customer_id, model_version) → prediction (customer_id, model_version) | Immutable forecast parameter version. Referenced input or derived key. |
| age_days | INTEGER | Yes | PK | Elapsed-day endpoint of the 30/90/180/365 window. Referenced input or derived key. |
| expected_cents | BIGINT | Yes | — | Cumulative expected contribution at the model age. Derived per mapping. |

## spend_allocation
Audited allocation components. One row per run_id, campaign_id, spend_date, allocation_method, signup_month.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| run_id | VARCHAR | Yes | PK; FK run_manifest.run_id | Immutable report snapshot identifier. Referenced input or derived key. |
| campaign_id | VARCHAR | Yes | PK; FK campaign.campaign_id; FK (campaign_id, spend_date, spend_recorded_at) → campaign_day (campaign_id, spend_date, recorded_at) | Campaign identifier. Referenced input or derived key. |
| spend_date | DATE | Yes | PK; FK (campaign_id, spend_date, spend_recorded_at) → campaign_day (campaign_id, spend_date, recorded_at) | UTC date to which source campaign spend belongs. Referenced input or derived key. |
| allocation_method | VARCHAR | Yes | PK | Calendar period or winning-touch weighting scenario. Referenced input or derived key. Values: CALENDAR, TOUCH_WEIGHT. |
| signup_month | DATE | Yes | PK | First UTC calendar date of the allocated or acquisition month. Referenced input or derived key. |
| spend_recorded_at | TIMESTAMPTZ | Yes | FK (campaign_id, spend_date, spend_recorded_at) → campaign_day (campaign_id, spend_date, recorded_at) | Version timestamp of the selected campaign-day source row. Referenced input or derived key. |
| allocated_cents | BIGINT | Yes | — | Share of campaign-day eligible spend assigned to this signup month. Derived per mapping. |
| winner_count | INTEGER | Conditional | — | Winning-touch count for TOUCH_WEIGHT, including zero for fallback. Null for CALENDAR. |
| lag_incomplete | BOOLEAN | Yes | — | Whether the full conversion window remains unobserved. Derived per mapping. |

## customer_age
Realized customer outcome. One row per run_id, customer_id, age_days.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| run_id | VARCHAR | Yes | PK; FK run_manifest.run_id | Immutable report snapshot identifier. Referenced input or derived key. |
| customer_id | VARCHAR | Yes | PK; FK acquisition.customer_id | Canonical acquired customer identifier. Referenced input or derived key. |
| age_days | INTEGER | Yes | PK | Elapsed-day endpoint of the 30/90/180/365 window. Referenced input or derived key. |
| horizon_end | TIMESTAMPTZ | Yes | — | Exclusive customer-age endpoint. Derived per mapping. |
| maturity | VARCHAR | Yes | — | Indicates whether the full age window is observed. Derived per mapping. Values: MATURE, PENDING. |
| revenue_cents | BIGINT | No | — | Sum of eligible signed revenue components in the outcome window. Derived per mapping. |
| cost_cents | BIGINT | No | — | Sum of attributable signed cost components in the outcome window. Derived per mapping. |
| contribution_cents | BIGINT | No | — | Eligible revenue minus attributable costs. Derived per mapping. |

## channel_cohort
Period and age reporting. One row per run_id, channel, signup_month, age_days, allocation_method, model_version.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| run_id | VARCHAR | Yes | PK; FK run_manifest.run_id | Immutable report snapshot identifier. Referenced input or derived key. |
| channel | VARCHAR | Yes | PK | Paid acquisition category or UNKNOWN for unresolved attribution. Referenced input or derived key. Values: GOOGLE_ADS, META_ADS, PAID_AFFILIATES, UNKNOWN. |
| signup_month | DATE | Yes | PK | First UTC calendar date of the allocated or acquisition month. Referenced input or derived key. |
| age_days | INTEGER | Yes | PK | Elapsed-day endpoint of the 30/90/180/365 window. Referenced input or derived key. |
| allocation_method | VARCHAR | Yes | PK | Calendar period or winning-touch weighting scenario. Referenced input or derived key. Values: CALENDAR, TOUCH_WEIGHT. |
| model_version | VARCHAR | Yes | PK; FK forecast_model.model_version | Immutable forecast parameter version. Referenced input or derived key. |
| cohort_status | VARCHAR | Yes | — | Mature, pending or spend-only reporting state. Derived per mapping. Values: MATURE, PENDING, SPEND_ONLY. |
| registrations | INTEGER | Yes | — | Distinct canonical signups at the output grain. Derived per mapping. |
| mature_customers | INTEGER | Yes | — | Canonical customers with complete age windows. Derived per mapping. |
| paid_attributed_customers | INTEGER | Yes | — | Signups assigned to an approved paid channel. Derived per mapping. |
| eligible_spend_cents | BIGINT | No | — | Eligible spend assigned to the output grain. Derived per mapping. |
| revenue_cents | BIGINT | No | — | Sum of eligible signed revenue components in the outcome window. Derived per mapping. |
| cost_cents | BIGINT | No | — | Sum of attributable signed cost components in the outcome window. Derived per mapping. |
| contribution_cents | BIGINT | No | — | Eligible revenue minus attributable costs. Derived per mapping. |
| expected_comparable_cents | BIGINT | No | — | Frozen expected contribution summed over the realized comparison population. Derived per mapping. |
| expected_all_cents | BIGINT | No | — | Frozen expected contribution summed over all registrations in the group. Derived per mapping. |
| cac_usd | DECIMAL(28,8) | No | — | Eligible spend in USD divided by aligned acquired customers. Derived per mapping. |
| revenue_per_customer_usd | DECIMAL(28,8) | No | — | Eligible recognized revenue in USD per comparable customer. Derived per mapping. |
| revenue_roas | DECIMAL(28,8) | No | — | Eligible recognized revenue divided by aligned eligible spend. Derived per mapping. |
| predicted_ltv_cac | DECIMAL(28,8) | No | — | Matched frozen first-year contribution divided by acquisition spend. Derived per mapping. |
| realized_per_spend | DECIMAL(28,8) | No | — | Matched realized contribution divided by acquisition spend. Derived per mapping. |
| after_spend_cents | BIGINT | No | — | Realized contribution less matched eligible acquisition spend. Derived per mapping. |
| paid_metric_status | VARCHAR | Yes | — | Paid metric eligibility or reason it is unavailable. Derived per mapping. Values: AVAILABLE, ZERO_DENOMINATOR, UNKNOWN_CHANNEL, SPEND_MISSING, PENDING. |

## campaign_performance_day
Operational campaign output. One row per run_id, campaign_id, report_date.

| Field | SQL type | Required | Key | Meaning and origin |
|---|---|---|---|---|
| run_id | VARCHAR | Yes | PK; FK run_manifest.run_id | Immutable report snapshot identifier. Referenced input or derived key. |
| campaign_id | VARCHAR | Yes | PK; FK campaign.campaign_id | Campaign identifier. Referenced input or derived key. |
| report_date | DATE | Yes | PK | UTC calendar day in campaign operations. Referenced input or derived key. |
| actual_cents | BIGINT | No | — | Actual campaign spend for the source or report day. Derived per mapping. |
| eligible_spend_cents | BIGINT | No | — | Eligible spend assigned to the output grain. Derived per mapping. |
| planned_cents | BIGINT | No | — | Planned spend for the source or report day. Derived per mapping. |
| registrations | INTEGER | Yes | — | Distinct canonical signups at the output grain. Derived per mapping. |
| mature_30_customers | INTEGER | Yes | — | Daily signups with an observable full 30-day window. Derived per mapping. |
| activated_30_customers | INTEGER | Yes | — | Mature daily signups with at least one qualifying product. Derived per mapping. |
| baseline_forecast_total_cents | BIGINT | Yes | — | Sum of baseline first-year forecasts for daily assigned signups. Derived per mapping. |
| cac_usd | DECIMAL(28,8) | No | — | Eligible spend in USD divided by aligned acquired customers. Derived per mapping. |
| actual_to_date_cents | BIGINT | No | — | Sum of actual spend from applicable period start through report date. Derived per mapping. |
| plan_to_date_cents | BIGINT | No | — | Cumulative plan from applicable period start through report date. Derived per mapping. |
| remaining_budget_cents | BIGINT | No | — | Period cap less cumulative actual spend. Derived per mapping. |
| pace_ratio | DECIMAL(28,8) | No | — | Cumulative actual divided by cumulative positive plan. Derived per mapping. |
| activation_rate | DECIMAL(28,8) | No | — | Activated divided by mature eligible signups. Derived per mapping. |
| data_status | VARCHAR | Yes | — | Operational input readiness state. Derived per mapping. Values: READY, MISSING_PLAN, MISSING_SPEND, INCOMPLETE. |
| pacing_status | VARCHAR | Yes | — | Flag, OK or unavailable based on pacing inputs. Derived per mapping. Values: FLAG, OK, UNAVAILABLE. |
