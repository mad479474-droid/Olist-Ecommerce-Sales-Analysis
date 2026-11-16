# Windows quick start — SQL Server 2022 (no Import Wizard needed)

## Current situation
You have **already run `sql/01_schema.sql`** and the eight `dbo` tables exist in `OlistTrackA`. You do **NOT** need to run `01_schema.sql` again. The old `dbo.stg_customers` table from the wizard can be ignored. We deliberately import directly to the original eight `dbo` tables.

## Step 1 — Copy project and original Dataset
Extract this ZIP project anywhere (e.g. `Desktop\project bi\Track_A_Olist_Sales`) and keep the original Olist CSVs unchanged in `Desktop\project bi\Dataset`. Do **not** copy or edit the CSVs in Excel.

## Step 2 — Execute a single command (PowerShell)
From the extracted project folder, hold **Shift**, right-click blank space, and choose **Open PowerShell window here** or open PowerShell and `cd` into the project folder.

Copy this command (change only the folder path if yours is different):

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\tools\import_olist_sqlserver.ps1" -DataFolder "C:\Users\Dell\Desktop\project bi\Dataset" -Server "."
```

The command connects using your **Windows account** to SQL Server `.` and imports all eight CSV files straight into their prepared tables. No passwords or new staging tables. The program checks every table's expected row count, skips fully loaded tables, and **stops** if it finds partial data (it never deletes anything automatically). It handles quoted commas, multiline review text, leading-zero zip codes and nullable timestamps.

> If your SQL Server instance uses a different name, change `-Server "."` to the exact working instance. If the terminal reports an error, capture the **full red error text** and report it before retrying. On success it prints `ALL EIGHT TABLES IMPORTED AND COUNTS VERIFIED.`

## Step 3 — Validation in SSMS
Select database **OlistTrackA**, then open and execute files in this exact order:

1. `sql/02_validation.sql` — check counts / duplicates / missing keys; read any warnings.
2. `sql/00_views.sql` — create reusable analysis views.
3. `sql/03_analysis.sql` — run all twelve questions.
4. `sql/04_dashboard_exports.sql` — reproduce dashboard source datasets.

SQL Server 2022 is required; do not run the same schema creation script twice. After import, verify expected counts:

```sql
USE OlistTrackA;
SELECT 'customers' name,COUNT_BIG(*) n FROM dbo.customers
UNION ALL SELECT 'orders',COUNT_BIG(*) FROM dbo.orders
UNION ALL SELECT 'order_items',COUNT_BIG(*) FROM dbo.order_items
UNION ALL SELECT 'products',COUNT_BIG(*) FROM dbo.products
UNION ALL SELECT 'sellers',COUNT_BIG(*) FROM dbo.sellers
UNION ALL SELECT 'order_payments',COUNT_BIG(*) FROM dbo.order_payments
UNION ALL SELECT 'order_reviews',COUNT_BIG(*) FROM dbo.order_reviews
UNION ALL SELECT 'category_translation',COUNT_BIG(*) FROM dbo.category_translation;
```

Expected row counts respectively: 99,441; 99,441; 112,650; 32,951; 3,095; 103,886; 99,224; 71.

## Step 4 — Excel and GitHub
Open `dashboard/Track_A_Sales_Dashboard.xlsx` in desktop Excel. Year filter is at `Dashboard!B4`, month filter at `Dashboard!E4`. These are **editable cell dropdowns with SUMIFS formulas**, not PivotTable slicers or a live SQL connection. Charts change as filters change. The workbook contains a snapshot based on the original CSVs, and is readable without SQL Server. The SQL export script `sql/04_dashboard_exports.sql` reproduces the source data. To update the snapshot with a changed dataset, export these SQL results and refresh the respective `SQL_Daily`/`SQL_Monthly` worksheets. Make sure all charts and reconciliation are still correct after refreshing.

The raw CSVs are **not included** in the GitHub-ready ZIP; the README links the original data source. Upload the extracted project folder to your own repository. Add team-member contributions truthfully before the final hand-in.

## Why the old staging table was not used
The previous SSMS screen showed `dbo.stg_customers` in Object Explorer, but `SELECT` on it returned `Invalid object name`; `OBJECT_ID` was NULL from the query session. Its exact cause is **not confirmed**, so the import script avoids that staging table altogether. The script will still require the original database/table names to be available from the selected connection.

## Validation scope
The existing numerical snapshots were calculated from the **original Olist CSVs locally**, not by executing T-SQL on your actual SQL Server. Only a live SSMS run can establish that your local SQL Server import and queries complete successfully.
