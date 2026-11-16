# Olist Sales Trends — Business Intelligence SQL Project (Track A)

**Track:** A — Sales trends. **SQL dialect:** Microsoft SQL Server 2022 / T-SQL. **Excel dashboard:** `.xlsx`, editable; verify your Excel application/version before presentation. **Time scope:** purchase dates `2017-01-01` inclusive through `2018-09-01` exclusive. **Currency:** Brazilian real (BRL). **Population:** delivered orders for merchandise sales and most sales analyses; all order statuses for G1 and A5.

## Business objective

Help a marketplace sales manager understand how merchandise sales and delivered-order volumes change month to month, which weekdays are busiest, how the first and second halves of a month differ, and what product categories contribute to the busiest months. Business interpretations are descriptive, not causal.

## Verified headline findings (original Olist data)

- **96,211** delivered orders within the purchase-date scope, out of **99,092** orders of all statuses.
- **BRL 13,181,027.13** delivered merchandise sales (excludes freight); **BRL 137.00** delivered-order AOV.
- **November 2017** was the top sales month: **BRL 987,765.37**.
- Jan-Aug 2018 merchandise sales grew **141.13%** over Jan-Aug 2017. AOVs were similar, so order-volume growth explains much of this aggregate difference.
- Monday averaged **BRL 24,888.55** merchandise sales per calendar Monday in the scope.
- There were **643** delivered orders with no selected valid review; no delivered orders lacked a payment record in scope.

For evidence and caveats, see [`report/Track_A_Findings.pdf`](report/Track_A_Findings.pdf) and [`results/`](results/).

![Track A Excel dashboard](dashboard/dashboard_preview.png)

## ONE-COMMAND WINDOWS IMPORT (NEW)

If the SSMS Import Data option is unavailable or an `stg_customers` staging table gives `Invalid object name`, **do not keep using that staging table**. Read [`docs/QUICK_START_WINDOWS.md`](docs/QUICK_START_WINDOWS.md) for a PowerShell importer that loads the eight original CSVs directly into the existing SQL Server 2022 tables, verifies counts, and does not delete or overwrite existing rows. The direct-import script is [`tools/import_olist_sqlserver.ps1`](tools/import_olist_sqlserver.ps1). No ODBC driver, Python installation, or Import Wizard is needed on Windows PowerShell.

## Deliverables and run order

| Step | Path | What it does |
|---|---|---|
| 1 | `sql/01_schema.sql` | Create OlistTrackA database, 8 source tables, keys/indexes (once only) |
| 2 | `docs/QUICK_START_WINDOWS.md` | Direct PowerShell import to existing SQL Server tables (recommended); verify counts |
| 3 | `sql/02_validation.sql` | Check source row counts, unmatched keys, invalid/negative values, duplicate reviews |
| 4 | `sql/00_views.sql` | Create review-per-order, item-per-order, payment-per-order, scope/delivered views |
| 5 | `sql/03_analysis.sql` | All 12 Qs: G1-G3, A1-A7, O1-O2 |
| 6 | `sql/04_dashboard_exports.sql` | SQL daily/monthly data source with month and year dimensions |
| 7 | `dashboard/Track_A_Sales_Dashboard.xlsx` | Dashboard + 4+ KPIs + charts + Year/Month dropdown filters + reconciliation |
| 8 | `report/Track_A_Findings.pdf` | Scenario, compact evidence for 12 questions, 6 findings, 3 actions, limits |
| Docs | `docs/ER_Diagram.png`, `docs/DATA_DICTIONARY.md`, `docs/SQL_coverage_map.csv` | Schema and definitions |

## Questions answered

- **G1** Order counts/status distribution + delivered sales/AOV; **G2** monthly sales, growth and running total; **G3** missing review/payment coverage.
- **A1** Year-over-year Jan-Aug; **A2** weekday demand normalized by calendar days; **A3** daily sales above same-month calendar-day average; **A4** category sales of top 3 months; **A5** status mix by month; **A6** daily versus same weekday previous week; **A7** first half versus second half of month.
- **O1** Which quarters have the widest within-quarter monthly sales range? **O2** How do weekday and weekend sales per calendar day compare?

## Downloading data and SQL Server setup

1. Obtain the original **Olist Brazilian E-Commerce Public Dataset** from https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce. The eight required files are: `olist_customers_dataset.csv`, `olist_orders_dataset.csv`, `olist_order_items_dataset.csv`, `olist_products_dataset.csv`, `olist_sellers_dataset.csv`, `olist_order_payments_dataset.csv`, `olist_order_reviews_dataset.csv`, and `product_category_name_translation.csv`. Geolocation is optional.
2. Preserve CSV bytes as downloaded; **raw datasets are intentionally not included in GitHub**. Extract to local `data/raw/`.
3. Follow [`docs/IMPORT_SQL_SERVER.md`](docs/IMPORT_SQL_SERVER.md) to create/import and then run the SQL files in the above order, in **SQL Server Management Studio (SSMS)** against SQL Server 2022.
4. Export SQL result grids as CSV with column headers and compare with the provided aggregates under `results/`.
5. Open the workbook in desktop Excel. Change `Dashboard!B4` (year) and `Dashboard!E4` (month) dropdowns. All KPI cards and charts recalculate from populated SQL-derived daily/monthly fact tables. `Read_Me` describes refresh, `Reconciliation` cross-checks default All/All against exports. If refreshing data, replace the source table rows with SQL export rows and preserve formulas / table extents.

**Validation note:** The provided original CSVs were processed and verified with a local SQLite-based extraction/cross-check. **No SQL Server 2022 instance was available for a live SSMS execution test in the authoring environment.** Before presentation run the SQL files in SSMS and confirm row counts and values, especially the import review text and timestamps. The `.xlsx` was generated and year+month filter combinations were tested locally.

## SQL topic coverage

See [`docs/SQL_coverage_map.csv`](docs/SQL_coverage_map.csv). The answer scripts include 3+ table join, LEFT JOIN, self-join, scalar / multi-row / derived / correlated subqueries, EXISTS/NOT EXISTS, CTEs, ROW_NUMBER/DENSE_RANK, LAG and cumulative SUM OVER.

## Business / dataset limitations

- The dataset covers a historical 2016-2018 period, but project metrics use the purchase window ending Aug 2018. Some outcomes are incomplete near the end of the snapshot.
- The sales figures measure item prices for delivered orders, **not profit** or platform commission; freight is excluded.
- We cannot infer true lifetime retention, causation, marketing ROI, refunds, or current sales trends.
- Orders can have multiple item, payment and source review rows; `v_order_items_total` and `v_order_payments_total` are pre-aggregated to a single order row, and `v_analysis_review` selects the latest valid review with documented ordering.
- Quarter 2018-Q3 includes only two observed purchase months (Jul–Aug), making intra-quarter range comparisons with complete quarters limited.

## Team and contributions (complete before submitting)

- Team name: `[insert name]`
- Members: `[insert member names]`
- Contributions: `[insert truthful role-by-role contributions after team review]`
- Exact Excel application/version on delivery machine: `[record]`
- CSV download date: `[record]`

## Tools and sources

Data: Olist, *Brazilian E-Commerce Public Dataset*, https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce, listed **CC BY-NC-SA 4.0** in the course brief. SQL Server 2022; Excel .xlsx; Python's csv/sqlite3/reportlab; artifact_tool for workbook generation; Graphviz for ER diagram. See project brief and course SQL sections. No credentials or personal database connection required to open the dashboard.
