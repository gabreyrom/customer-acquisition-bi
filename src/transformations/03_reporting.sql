CREATE TEMP TABLE checkpoints(age_days INTEGER);
INSERT INTO checkpoints VALUES (30),(90),(180),(365);
CREATE TEMP TABLE products(product VARCHAR);
INSERT INTO products VALUES ('SAVINGS'),('DEBIT'),('CREDIT'),('PERSONAL'),('MORTGAGE');

INSERT INTO activation
WITH refunds AS (
 SELECT original_source_key,sum(amount_cents) reduction FROM accepted_purchase_refund
 GROUP BY original_source_key
), qualifying AS (
 SELECT d.customer_id,d.product,d.effective_at,d.source_key
 FROM activity d JOIN acquisition a USING(customer_id)
 LEFT JOIN refunds f ON f.original_source_key=d.source_key
 WHERE d.status='ACCEPTED' AND d.state='SETTLED' AND d.effective_at>=a.registration_at
 AND d.effective_at<a.registration_at+INTERVAL 30 DAY AND (
   (d.product='SAVINGS' AND d.activity_code='DEP_SETTLED' AND d.amount_cents>=1000)
   OR (d.product IN ('DEBIT','CREDIT') AND d.activity_code='PURCHASE_SETTLED' AND d.amount_cents>coalesce(f.reduction,0))
   OR (d.product IN ('PERSONAL','MORTGAGE') AND d.activity_code='LOAN_FUNDING' AND d.amount_cents>0))
 QUALIFY row_number() OVER(PARTITION BY d.customer_id,d.product ORDER BY effective_at,source_key)=1
)
SELECT run_id,a.customer_id,p.product,q.effective_at,q.source_key,
 CASE WHEN q.source_key IS NOT NULL THEN 'QUALIFIED'
      WHEN a.registration_at+INTERVAL 30 DAY>effective_cutoff THEN 'PENDING'
      ELSE 'NO_QUALIFYING_EVENT' END
FROM acquisition a CROSS JOIN products p CROSS JOIN run_manifest
LEFT JOIN qualifying q ON q.customer_id=a.customer_id AND q.product=p.product;

INSERT INTO customer_age
WITH windows AS (
 SELECT r.run_id,a.customer_id,c.age_days,a.registration_at,
        a.registration_at+to_days(c.age_days) horizon, horizon<=r.effective_cutoff mature
 FROM acquisition a CROSS JOIN checkpoints c CROSS JOIN run_manifest r
), sums AS (
 SELECT w.*,coalesce(sum(f.signed_cents) FILTER(WHERE f.class='REVENUE'),0) revenue,
            coalesce(sum(f.signed_cents) FILTER(WHERE f.class='COST'),0) cost
 FROM windows w LEFT JOIN financial_event f ON f.run_id=w.run_id AND f.customer_id=w.customer_id
 AND f.effective_at>=w.registration_at AND f.effective_at<w.horizon AND w.mature
 GROUP BY ALL
)
SELECT run_id,customer_id,age_days,horizon,CASE WHEN mature THEN 'MATURE' ELSE 'PENDING' END,
       CASE WHEN mature THEN revenue END,CASE WHEN mature THEN cost END,
       CASE WHEN mature THEN revenue-cost END
FROM sums;

CREATE TEMP VIEW cohort_input AS
SELECT a.customer_id,a.signup_month,t.channel,t.campaign_id,h.age_days,h.maturity,
       h.revenue_cents,h.cost_cents,h.contribution_cents,p.model_version,p.expected_cents,
       s.expected_365_cents
FROM acquisition a JOIN attribution t USING(customer_id) JOIN customer_age h USING(customer_id)
JOIN prediction_age p ON p.customer_id=h.customer_id AND p.age_days=h.age_days
JOIN prediction s ON s.customer_id=p.customer_id AND s.model_version=p.model_version;

INSERT INTO channel_cohort
WITH people AS (
 SELECT channel,signup_month,age_days,model_version,count(*) n,
   count(*) FILTER(WHERE maturity='MATURE') mn,
   coalesce(sum(revenue_cents),0) revenue,coalesce(sum(cost_cents),0) cost,
   sum(expected_cents) FILTER(WHERE maturity='MATURE') comparable,
   sum(expected_cents) expected,sum(expected_365_cents) headline
 FROM cohort_input GROUP BY ALL
), spend AS (
 SELECT c.channel,s.signup_month,s.allocation_method,sum(s.allocated_cents) cents
 FROM spend_allocation s JOIN campaign c USING(campaign_id) GROUP BY ALL
), methods AS (SELECT unnest(['CALENDAR','TOUCH_WEIGHT']) AS allocation_method),
grid AS (
 SELECT coalesce(p.channel,s.channel) channel,coalesce(p.signup_month,s.signup_month) signup_month,
        coalesce(p.allocation_method,s.allocation_method) allocation_method,coalesce(p.age_days,s.age_days) age_days,
        coalesce(p.model_version,s.model_version) model_version,
        coalesce(p.n,0) n,coalesce(p.mn,0) mn,p.revenue,p.cost,p.comparable,p.expected,p.headline,s.cents
 FROM (people CROSS JOIN methods) p FULL OUTER JOIN
      (spend CROSS JOIN checkpoints CROSS JOIN (SELECT model_version FROM forecast_model)) s
 USING(channel,signup_month,allocation_method,age_days,model_version)
), tagged AS (
 SELECT g.*,r.run_id,
 CASE WHEN n=0 THEN 'SPEND_ONLY'
      WHEN signup_month+INTERVAL 1 MONTH+to_days(age_days)<=effective_cutoff THEN 'MATURE'
      ELSE 'PENDING' END state
 FROM grid g CROSS JOIN run_manifest r
)
SELECT run_id,channel,signup_month,age_days,allocation_method,model_version,state,n,mn,
 CASE WHEN channel='UNKNOWN' THEN 0 ELSE n END,cents,
 CASE WHEN state='MATURE' THEN revenue END,CASE WHEN state='MATURE' THEN cost END,
 CASE WHEN state='MATURE' THEN revenue-cost END,
 CASE WHEN state='MATURE' THEN comparable END,expected,
 exact_ratio(cents,n*100,8),
 CASE WHEN state='MATURE' THEN exact_ratio(revenue,n*100,8) END,
 CASE WHEN state='MATURE' AND age_days=90 THEN exact_ratio(revenue,cents,8) END,
 exact_ratio(headline,cents,8),
 CASE WHEN state='MATURE' THEN exact_ratio(revenue-cost,cents,8) END,
 CASE WHEN state='MATURE' AND cents IS NOT NULL THEN revenue-cost-cents END,
 CASE WHEN n=0 OR cents=0 THEN 'ZERO_DENOMINATOR'
      WHEN channel='UNKNOWN' THEN 'UNKNOWN_CHANNEL' WHEN cents IS NULL THEN 'SPEND_MISSING'
      WHEN state='PENDING' THEN 'PENDING' ELSE 'AVAILABLE' END
FROM tagged;

INSERT INTO campaign_performance_day
WITH daily_people AS (
 SELECT t.campaign_id,a.signup_date report_date,count(*) n,
 count(*) FILTER(WHERE h.maturity='MATURE') mature,
 count(*) FILTER(WHERE h.maturity='MATURE' AND q.customer_id IS NOT NULL) activated,
 sum(f.expected_365_cents) forecast
 FROM acquisition a JOIN attribution t USING(customer_id)
 JOIN customer_age h ON h.customer_id=a.customer_id AND h.age_days=30
 JOIN prediction f ON f.customer_id=a.customer_id AND f.model_version='A_v0.3_BASELINE'
 LEFT JOIN (SELECT DISTINCT customer_id FROM activation WHERE status='QUALIFIED') q ON q.customer_id=a.customer_id
 WHERE t.campaign_id IS NOT NULL GROUP BY ALL
), days AS (
 SELECT c.campaign_id,g.report_date::DATE report_date,r.run_id,r.recorded_cutoff,r.effective_cutoff
 FROM campaign c CROSS JOIN run_manifest r
 CROSS JOIN LATERAL range(c.active_from::TIMESTAMP,
   least(coalesce(c.active_through+1,r.effective_cutoff::DATE),r.effective_cutoff::DATE)::TIMESTAMP,INTERVAL 1 DAY) g(report_date)
), combined AS (
 SELECT d.*,s.actual_cents,s.eligible_cents,s.planned_cents,
        coalesce(p.n,0) n,coalesce(p.mature,0) mature,coalesce(p.activated,0) activated,coalesce(p.forecast,0) forecast,
        b.budget_cents,coalesce(b.period_start,date_trunc('month',d.report_date)::DATE) period_start
 FROM days d LEFT JOIN daily_spend s ON s.campaign_id=d.campaign_id AND s.spend_date=d.report_date
 LEFT JOIN daily_people p ON p.campaign_id=d.campaign_id AND p.report_date=d.report_date
 LEFT JOIN LATERAL (
   SELECT * FROM campaign_budget b WHERE b.campaign_id=d.campaign_id AND b.period_kind='MONTH'
    AND d.report_date>=period_start AND d.report_date<period_end_exclusive AND b.recorded_at<=d.recorded_cutoff
    ORDER BY period_start DESC,b.recorded_at DESC LIMIT 1
 ) b ON true
), cumulative AS (
 SELECT x.*,
    CASE WHEN count(actual_cents) OVER w=report_date-period_start+1 THEN sum(actual_cents) OVER w END actual_td,
    CASE WHEN count(planned_cents) OVER w=report_date-period_start+1 THEN sum(planned_cents) OVER w END plan_td
 FROM combined x WINDOW w AS (PARTITION BY campaign_id,period_start ORDER BY report_date ROWS UNBOUNDED PRECEDING)
)
SELECT run_id,campaign_id,report_date,actual_cents,eligible_cents,planned_cents,n,mature,activated,forecast,
 exact_ratio(eligible_cents,n*100,8),actual_td,plan_td,budget_cents-actual_td,
 exact_ratio(actual_td,plan_td,8),exact_ratio(activated,mature,8),
 CASE WHEN actual_cents IS NULL THEN 'MISSING_SPEND' WHEN plan_td IS NULL THEN 'MISSING_PLAN'
      WHEN actual_td IS NULL OR mature<n THEN 'INCOMPLETE' ELSE 'READY' END,
 CASE WHEN actual_td IS NULL OR plan_td IS NULL OR plan_td<=0 THEN 'UNAVAILABLE'
      WHEN actual_td*10>plan_td*11 THEN 'FLAG' ELSE 'OK' END
FROM cumulative;
