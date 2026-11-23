# Acquisition and customer value · simplified ER diagram

```mermaid
erDiagram
    S_CAMPAIGN o|--o{ D_ACQUISITION : attributes
    S_IDENTITY ||--o{ D_ACQUISITION : resolves
    S_IDENTITY ||--o{ S_PRODUCT_ACCOUNT : identifies
    S_PRODUCT_ACCOUNT ||--o{ S_FINANCIAL_ACTIVITY : records
    S_FINANCIAL_ACTIVITY ||--o{ D_FINANCIAL_EVENT : standardizes
    D_ACQUISITION ||--o{ D_FINANCIAL_EVENT : owns
    D_ACQUISITION ||--o{ D_FIXED_LTV : scores
    D_ACQUISITION ||--o{ D_CUSTOMER_HISTORY : tracks
    D_FINANCIAL_EVENT }o--o{ D_CUSTOMER_HISTORY : contributes
    D_CUSTOMER_HISTORY }o--o{ D_REPORTING_MART : aggregates
    D_FIXED_LTV }o--o{ D_REPORTING_MART : benchmarks
    S_CAMPAIGN }o--o{ D_REPORTING_MART : supplies-spend
```

**S** marks a source entity and **D** marks a derived entity. The acquisition entity includes attribution and the campaign group includes marketing touches, spend and plans. The financial-event link to history represents effective-date aggregation across checkpoints. Reporting marts are cohort and campaign aggregates. The [detailed logical ER diagrams](logical_erd.md) show the physical lineage behind these groupings.
