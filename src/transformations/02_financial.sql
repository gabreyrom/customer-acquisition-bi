CREATE TEMP TABLE delivery_rank AS
SELECT d.*,
  row_number() OVER(PARTITION BY source_key ORDER BY recorded_at,delivery_id) position,
  count(DISTINCT struct_pack(account_id:=account_id,activity_code:=activity_code,effective_at:=effective_at,
    state:=state,amount_cents:=amount_cents,annual_rate:=annual_rate,balance_kind:=balance_kind,
    original_source_key:=original_source_key,adjustment_kind:=adjustment_kind,component:=component))
    OVER(PARTITION BY source_key) variants
FROM product_activity_delivery d CROSS JOIN run_manifest
WHERE d.recorded_at<=recorded_cutoff AND effective_at<effective_cutoff;

INSERT INTO exception_log
SELECT run_id,'product_activity_delivery',delivery_id,reason,recorded_cutoff,json_object('source_key',source_key)
FROM (
 SELECT delivery_id,source_key,CASE WHEN variants>1 THEN 'CONFLICTING_SOURCE_KEY' ELSE 'DUPLICATE_DELIVERY' END reason
 FROM delivery_rank WHERE variants>1 OR position>1
 UNION ALL
 SELECT delivery_id,source_key,'LATE_RECORD' FROM product_activity_delivery CROSS JOIN run_manifest
 WHERE recorded_at>recorded_cutoff AND effective_at<effective_cutoff
) e CROSS JOIN run_manifest;

CREATE TEMP TABLE activity_owner AS
SELECT d.delivery_id,count(DISTINCT l.canonical_customer_id) owners,min(a.customer_id) customer_id
FROM delivery_rank d JOIN product_account p USING(account_id) CROSS JOIN run_manifest r
LEFT JOIN LATERAL (
 SELECT * FROM identity_link l WHERE l.identity_key=p.owner_identity AND l.effective_from<=d.effective_at
   AND l.recorded_at<=r.recorded_cutoff
 QUALIFY row_number() OVER(PARTITION BY identity_key,canonical_customer_id,effective_from
    ORDER BY recorded_at DESC,identity_link_id DESC)=1
) l ON l.link_state='CANDIDATE' AND (l.effective_to IS NULL OR d.effective_at<l.effective_to)
LEFT JOIN acquisition a ON a.customer_id=l.canonical_customer_id AND a.registration_at<=d.effective_at
WHERE d.position=1 AND d.variants=1
  AND p.recorded_at<=r.recorded_cutoff AND d.effective_at>=p.opened_at
  AND (p.closed_at IS NULL OR d.effective_at<p.closed_at)
GROUP BY d.delivery_id;

INSERT INTO canonical_activity
SELECT run_id,d.source_key,d.delivery_id,d.account_id,CASE WHEN o.owners=1 AND o.customer_id IS NOT NULL THEN o.customer_id END,
       CASE WHEN o.owners=1 AND o.customer_id IS NOT NULL THEN 'ACCEPTED' ELSE 'OWNER_UNRESOLVED' END
FROM delivery_rank d LEFT JOIN activity_owner o USING(delivery_id) CROSS JOIN run_manifest
WHERE d.position=1 AND d.variants=1;

INSERT INTO exception_log
SELECT c.run_id,'product_activity_delivery',c.delivery_id,
       CASE WHEN o.owners>1 THEN 'IDENTITY_AMBIGUOUS' ELSE 'IDENTITY_MISSING' END,
       recorded_cutoff,json_object('source_key',c.source_key)
FROM canonical_activity c LEFT JOIN activity_owner o USING(delivery_id)
JOIN run_manifest r USING(run_id) WHERE c.status='OWNER_UNRESOLVED';

CREATE TEMP TABLE codebook(product VARCHAR, code VARCHAR, class VARCHAR, basis VARCHAR);
INSERT INTO codebook VALUES
 ('SAVINGS','SAV_TREASURY_INCOME','REVENUE','SAV_SETTLED_TREASURY'),
 ('SAVINGS','SAV_DEPOSIT_INTEREST','COST','SAV_SETTLED_DEPOSITOR'),
 ('SAVINGS','SAV_FEE','REVENUE',NULL),('SAVINGS','SAV_SERVICE','COST',NULL),
 ('DEBIT','DEBIT_INTERCHANGE','REVENUE',NULL),('DEBIT','DEBIT_FEE','REVENUE',NULL),
 ('DEBIT','DEBIT_PROCESSING','COST',NULL),('DEBIT','DEBIT_REWARD','COST',NULL),
 ('DEBIT','DEBIT_FRAUD','COST',NULL),('DEBIT','DEBIT_SERVICE','COST',NULL),
 ('CREDIT','CREDIT_INTERCHANGE','REVENUE',NULL),('CREDIT','CREDIT_FEE','REVENUE',NULL),
 ('CREDIT','CREDIT_INTEREST','REVENUE','CREDIT_PERFORMING_REVOLVING'),
 ('CREDIT','CREDIT_FUNDING','COST','CREDIT_FUNDED'),('CREDIT','CREDIT_LOSS','COST',NULL),
 ('CREDIT','CREDIT_PROCESSING','COST',NULL),('CREDIT','CREDIT_REWARD','COST',NULL),
 ('CREDIT','CREDIT_SERVICE','COST',NULL),
 ('PERSONAL','PERSONAL_INTEREST','REVENUE','PERSONAL_PERFORMING_PRINCIPAL'),
 ('PERSONAL','PERSONAL_FUNDING','COST','PERSONAL_FUNDED'),('PERSONAL','PERSONAL_FEE','REVENUE',NULL),
 ('PERSONAL','PERSONAL_SERVICE','COST',NULL),('PERSONAL','PERSONAL_COLLECTION','COST',NULL),
 ('PERSONAL','PERSONAL_LOSS','COST',NULL),
 ('MORTGAGE','MORTGAGE_INTEREST','REVENUE','MORTGAGE_PERFORMING_PRINCIPAL'),
 ('MORTGAGE','MORTGAGE_FUNDING','COST','MORTGAGE_FUNDED'),('MORTGAGE','MORTGAGE_FEE','REVENUE',NULL),
 ('MORTGAGE','MORTGAGE_ORIGINATION','COST',NULL),('MORTGAGE','MORTGAGE_SERVICE','COST',NULL),
 ('MORTGAGE','MORTGAGE_LOSS','COST',NULL);

CREATE TEMP VIEW activity AS
SELECT c.run_id,c.customer_id,c.status,p.product,d.*
FROM canonical_activity c JOIN product_activity_delivery d USING(delivery_id)
JOIN product_account p ON p.account_id=c.account_id;

CREATE TEMP VIEW economic_input AS
SELECT a.*, b.class,b.basis,
 CASE WHEN b.code IS NULL THEN 'INVALID_CODE'
      WHEN state NOT IN ('POSTED','CONFIRMED','SETTLED')
        OR (ends_with(activity_code,'_LOSS') AND state<>'CONFIRMED') THEN 'INVALID_STATE'
      WHEN amount_cents IS NULL OR (b.basis IS NOT NULL AND
           (annual_rate IS NULL OR balance_kind IS DISTINCT FROM b.basis)) THEN 'INVALID_CODE' END violation
FROM activity a LEFT JOIN codebook b ON b.product=a.product AND b.code=a.activity_code
WHERE status='ACCEPTED' AND activity_code NOT IN
 ('ADJUSTMENT','DEP_SETTLED','WITHDRAWAL','PURCHASE_SETTLED','PURCHASE_REFUND',
  'LOAN_FUNDING','PRINCIPAL_REPAYMENT','INTEREST_RECEIPT');

INSERT INTO exception_log
SELECT run_id,'product_activity_delivery',delivery_id,violation,recorded_cutoff,json_object('source_key',source_key)
FROM economic_input JOIN run_manifest USING(run_id) WHERE violation IS NOT NULL;

INSERT INTO financial_event
SELECT run_id,source_key||'/'||activity_code,source_key,activity_code,account_id,customer_id,
 activity_code,class,CASE WHEN basis IS NULL THEN amount_cents
                         ELSE exact_ratio(amount_cents::HUGEINT*(annual_rate*100000000)::HUGEINT,36500000000,0)::BIGINT END,
 effective_at,recorded_at,NULL,NULL
FROM economic_input WHERE violation IS NULL;
