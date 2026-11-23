CREATE TEMP VIEW identity_resolution AS
SELECT r.registration_id, count(DISTINCT l.canonical_customer_id) AS matches,
       min(l.canonical_customer_id) AS customer_id
FROM registration r
LEFT JOIN LATERAL (
    SELECT * FROM identity_link l WHERE l.identity_key=r.registration_identity
      AND l.effective_from<=r.registration_at AND l.recorded_at<=r.registration_at
    QUALIFY row_number() OVER (PARTITION BY identity_key,canonical_customer_id,effective_from
        ORDER BY recorded_at DESC,identity_link_id DESC)=1
) l ON l.link_state='CANDIDATE' AND (l.effective_to IS NULL OR r.registration_at<l.effective_to)
WHERE r.state='VALID' AND r.recorded_at<=(SELECT recorded_cutoff FROM run_manifest)
  AND r.registration_at<(SELECT effective_cutoff FROM run_manifest)
GROUP BY r.registration_id;

INSERT INTO exception_log
SELECT run_id,'registration',registration_id,
       CASE WHEN matches=0 THEN 'IDENTITY_MISSING' ELSE 'IDENTITY_AMBIGUOUS' END,
       recorded_cutoff,'{}' FROM identity_resolution CROSS JOIN run_manifest WHERE matches<>1;

INSERT INTO acquisition
SELECT i.customer_id,r.registration_id,r.registration_at,r.registration_at::DATE,
       date_trunc('month',r.registration_at)::DATE
FROM identity_resolution i JOIN registration r USING(registration_id)
WHERE matches=1
QUALIFY row_number() OVER(PARTITION BY customer_id ORDER BY registration_at,registration_id)=1;

INSERT INTO attribution
WITH visitor AS (
 SELECT a.customer_id,count(DISTINCT l.canonical_customer_id) n,min(l.canonical_customer_id) owner
 FROM acquisition a JOIN registration r USING(registration_id)
 LEFT JOIN LATERAL (
   SELECT * FROM identity_link l WHERE l.identity_key=r.visitor_identity
      AND l.effective_from<=a.registration_at AND l.recorded_at<=a.registration_at
   QUALIFY row_number() OVER (PARTITION BY identity_key,canonical_customer_id,effective_from
                             ORDER BY recorded_at DESC,identity_link_id DESC)=1
 ) l ON l.link_state='CANDIDATE' AND (l.effective_to IS NULL OR a.registration_at<l.effective_to)
 GROUP BY a.customer_id
)
SELECT a.customer_id,t.touch_id,t.campaign_id,coalesce(t.channel,'UNKNOWN'),
       CASE WHEN v.n>1 THEN 'AMBIGUOUS_VISITOR_LINK'
            WHEN v.n=0 OR v.owner<>a.customer_id THEN 'MISSING_VISITOR_LINK'
            WHEN t.touch_id IS NULL THEN 'NO_ELIGIBLE_TOUCH' ELSE 'MATCHED' END,
       'last-touch-30d-v1.0',a.registration_at
FROM acquisition a JOIN registration r USING(registration_id) JOIN visitor v USING(customer_id)
LEFT JOIN LATERAL (
 SELECT m.touch_id,m.campaign_id,c.channel FROM marketing_touch m JOIN campaign c USING(campaign_id)
 WHERE m.visitor_identity=r.visitor_identity AND v.n=1 AND v.owner=a.customer_id
   AND m.state='ELIGIBLE' AND m.touched_at>=a.registration_at-INTERVAL 30 DAY
   AND m.touched_at<a.registration_at AND m.recorded_at<=a.registration_at
   AND m.touched_at::DATE>=c.active_from AND (c.active_through IS NULL OR m.touched_at::DATE<=c.active_through)
 ORDER BY m.touched_at DESC,m.touch_id LIMIT 1
) t ON true;

CREATE TEMP VIEW daily_spend AS
SELECT s.* FROM campaign_day s CROSS JOIN run_manifest
WHERE s.spend_date<effective_cutoff::DATE AND s.recorded_at<=recorded_cutoff
QUALIFY row_number() OVER (PARTITION BY campaign_id,spend_date ORDER BY s.recorded_at DESC)=1;

INSERT INTO exception_log
SELECT run_id,'campaign_day',campaign_id||'/'||spend_date,'MISSING_PLAN',recorded_cutoff,'{}'
FROM daily_spend CROSS JOIN run_manifest WHERE planned_cents IS NULL;

INSERT INTO spend_allocation
SELECT run_id,campaign_id,spend_date,'CALENDAR',date_trunc('month',spend_date)::DATE,
       recorded_at,eligible_cents,NULL,spend_date+31>effective_cutoff::DATE
FROM daily_spend CROSS JOIN run_manifest;

INSERT INTO spend_allocation
WITH winners AS (
 SELECT t.campaign_id,m.touched_at::DATE spend_date,a.signup_month,count(*) n
 FROM attribution t JOIN marketing_touch m USING(touch_id) JOIN acquisition a USING(customer_id)
 GROUP BY ALL
), inputs AS (
 SELECT s.*,coalesce(w.signup_month,date_trunc('month',s.spend_date)::DATE) target_month,
          coalesce(w.n,0) n,sum(coalesce(w.n,0)) OVER(PARTITION BY s.campaign_id,s.spend_date) total
 FROM daily_spend s LEFT JOIN winners w USING(campaign_id,spend_date)
), shares AS (
 SELECT *, CASE WHEN total=0 THEN eligible_cents ELSE eligible_cents::HUGEINT*n//total::HUGEINT END base,
        CASE WHEN total=0 THEN 0 ELSE eligible_cents::HUGEINT*n%total::HUGEINT END remainder
 FROM inputs
), ranked AS (
 SELECT *,sum(base) OVER(PARTITION BY campaign_id,spend_date) base_sum,
        row_number() OVER(PARTITION BY campaign_id,spend_date ORDER BY remainder DESC,target_month) priority
 FROM shares
)
SELECT run_id,campaign_id,spend_date,'TOUCH_WEIGHT',target_month,recorded_at,
       base + (priority<=eligible_cents-base_sum)::INT,n,spend_date+31>effective_cutoff::DATE
FROM ranked CROSS JOIN run_manifest;
