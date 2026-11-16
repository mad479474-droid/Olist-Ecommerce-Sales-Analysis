# SQL Server 2022 import / repeatable setup

1. Download original ZIP: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce. Extract the eight CSVs (geolocation optional) into a local `data/raw` folder. Do not edit originals.
2. In SSMS 2022, run `sql/01_schema.sql` **once** in an empty SQL Server instance/database. Then inspect column headings and names below before importing.
3. **Recommended reliable approach**: right-click the `OlistTrackA` database → Tasks → Import Data, using a Flat File Source (CSV/UTF-8, comma delimiter, `"` quotation handling, first row headers, ISO date/time format). Map columns **by header name**, not ordinal, to the already-created destination tables. For `order_reviews`, **omit the extra generated** `source_review_row_index` column: SQL Server supplies identity. Keep NULL for empty date columns. Use `DECIMAL(18,2)` for prices and payment values. If the wizard offers to recreate a table, cancel and use the existing schema.
4. Important: If CSV Import Wizard cannot correctly parse quoted commas/newlines in reviews, use SSIS Flat File Source with text qualifier `"` and UTF-8; validate loaded row counts before proceeding. `BULK INSERT ... FORMAT='CSV', CODEPAGE='65001'` is another SQL Server 2022 alternative, but identity-column mapping must be configured (for reviews use a staging table with exactly the CSV columns first, then `INSERT ... SELECT` into `dbo.order_reviews`).
5. Confirm imported row counts in `sql/02_validation.sql`: customers=99,441; orders=99,441; items=112,650; products=32,951; sellers=3,095; payments=103,886; reviews=99,224; category_translation=71. Examine rejects and unexpected NULLs.
6. Run `sql/00_views.sql` after validation. Run `sql/03_analysis.sql` and `sql/04_dashboard_exports.sql`. Use SSMS Results to File / Export Wizard to obtain CSVs with headers. Do not run all scripts more than once: `01_schema.sql` creates base tables.
7. Validate the final SQL dashboard metrics against `results/validation_summary.json`. The local cross-check here uses SQLite for independent extraction of the original CSVs; **T-SQL scripts were written for SQL Server 2022 but cannot be executed against an actual SQL Server instance in this environment**. Test them in SSMS on the presentation computer.

## Common import gotchas
- SQL Server may not be able to access CSVs on the *client* machine when using server-side BULK INSERT; copy CSVs onto a path accessible to SQL Server service and grant read access.
- Olist CSV source identifiers and zip prefixes are **text**, never numeric.
- Preserve the review text qualifier and multiline CSV semantics. Row count and spot-check against source before relying on result.
- `order_item_id` is an item sequence, not quantity; count item rows.
- Do not join item rows to payment rows without pre-aggregation.
