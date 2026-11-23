# Logical entity relationships

```mermaid
erDiagram
  REGISTRATION ||--o{ REGISTRATION_FEATURE : captures
  REGISTRATION ||--o| ACQUISITION : resolves
  IDENTITY_LINK }o--o{ REGISTRATION : matches
  IDENTITY_LINK }o--o{ PRODUCT_ACCOUNT : resolves
  ACQUISITION ||--|| ATTRIBUTION : fixes
  CAMPAIGN ||--o{ MARKETING_TOUCH : receives
  MARKETING_TOUCH o|--o{ ATTRIBUTION : wins
  CAMPAIGN ||--o{ CAMPAIGN_DAY : spends
  CAMPAIGN ||--o{ CAMPAIGN_BUDGET : plans
  CAMPAIGN_DAY ||--o{ SPEND_ALLOCATION : distributes
```

```mermaid
erDiagram
  PRODUCT_ACCOUNT ||--o{ PRODUCT_ACTIVITY_DELIVERY : owns
  PRODUCT_ACTIVITY_DELIVERY ||--o{ CANONICAL_ACTIVITY : selected
  CANONICAL_ACTIVITY ||--o{ FINANCIAL_EVENT : maps
  FINANCIAL_EVENT o|--o{ FINANCIAL_EVENT : adjusts
  ACQUISITION ||--o{ FINANCIAL_EVENT : receives
  ACQUISITION ||--o{ ACTIVATION : qualifies
  ACQUISITION ||--o{ CUSTOMER_AGE : measures
  ACQUISITION ||--|| FEATURE_SNAPSHOT : freezes
  FEATURE_SNAPSHOT ||--o{ PREDICTION : scores
  FORECAST_MODEL ||--o{ PREDICTION : versions
  PREDICTION ||--|{ PREDICTION_AGE : profiles
```

Customer-age rows, attribution, forecast trajectories and spend allocations aggregate independently before the channel cohort join. Campaign performance combines daily spend and applicable budget plans with daily signup attribution and customer-level activation. The run manifest scopes ledger and reporting relations, while exception rows retain source identifiers. Physical keys and join constraints live in the data contract.
