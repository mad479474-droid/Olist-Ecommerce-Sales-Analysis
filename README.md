# Olist E-Commerce | Business Intelligence — Track A: Sales Trends

A Business Intelligence project that analyzes historical sales trends in the **Olist Brazilian E-Commerce Dataset** using **Microsoft SQL Server 2022 (T-SQL)** and presents SQL-derived results in an interactive **Microsoft Excel Dashboard**.

## Team

- حمدي عماد ممدوح احمد
- زياد حمدي محمود السقا
- امير عرابي الهواري
- يوسف محمود عبد الاله محمد

## Business scenario

A marketplace sales manager wants to understand how order volume and merchandise revenue change by month, year and weekday, spot high-performing days and product categories, and use these findings to support staffing, campaign planning and reporting decisions.

**Analysis period:** January 1, 2017–August 31, 2018 (based on the order purchase timestamp). **Sales metric:** sum of item prices for *delivered* orders, excluding shipping/freight, in Brazilian reais (BRL). This is historical analysis, not current performance or profit.

## Project deliverables

- **12 SQL questions:** 3 general questions (G1–G3), 7 Track A questions (A1–A7), and 2 additional questions (O1–O2).
- **T-SQL techniques:** JOINs, subqueries (including EXISTS / NOT EXISTS), CTEs, and window functions.
- **Excel Dashboard:** four key metrics, four charts, and two dropdown filters (year and month).
- **Documentation:** ER diagram, data dictionary, validation results, business report, and analysis result exports.

## Repository contents

> **Important:** In this GitHub repository, the files were uploaded into the **repository root**, not their original local folders. The paths below reflect the *current GitHub layout*.

| File | Purpose |
| --- | --- |
| `01_schema.sql` | Create database `OlistTrackA` and its eight core tables |
| `02_validation.sql` | Verify row counts, missing relationships, dates and data-quality checks |
| `00_views.sql` | Create reusable analysis views |
| `03_analysis.sql` | All 12 analysis questions, including optimized G3 |
| `04_dashboard_exports.sql` | Produce data used to reconcile or refresh the dashboard |
| `import_olist_sqlserver.ps1` | Import the eight CSV files directly into SQL Server |
| `Track_A_Sales_Dashboard.xlsx` | Interactive Excel dashboard |
| `Track_A_Findings.pdf` | Business scenario, insights and recommendations |
| `ER_Diagram.png`, `DATA_DICTIONARY.md` | Database diagram and definitions |
| `G1_*.csv`, `G2_*.csv`, `G3_*.csv`, `A*.csv`, `O*.csv` | Analysis results |
| `Dashboard_daily.csv`, `dashboard_monthly.csv` | Dashboard source summaries |
| `QUICK_START_WINDOWS.md`, `IMPORT_SQL_SERVER.md` | Additional setup instructions |

## Requirements

- Microsoft SQL Server 2022
- SQL Server Management Studio (SSMS)
- Windows PowerShell 5.1+
- Microsoft Excel (desktop version for interactive dropdowns and charts)
- Original Olist CSV dataset downloaded separately

## Get the dataset

Download the **Brazilian E-Commerce Public Dataset by Olist** from:

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce

Extract the original CSV files into a local folder, for example:

`C:\Users\Dell\Desktop\project bi\Dataset`

The raw CSV files are **not included in this repository**. Do not open and resave the source CSV files in Excel before importing.

## Run the project

### 1. Create the database

Connect to your SQL Server instance in SSMS using Windows Authentication. Open and execute `01_schema.sql` **once** on a fresh database setup. It creates the `OlistTrackA` database and eight core tables.

**If `OlistTrackA` and its tables already exist, do not run this script again.**

### 2. Import the CSV files

Open Windows PowerShell in the directory where `import_olist_sqlserver.ps1` is saved. For files downloaded directly from this GitHub repository (flat root layout), run:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ".\import_olist_sqlserver.ps1" -DataFolder "C:\Users\Dell\Desktop\project bi\Dataset" -Server "."
```

If you're instead using the **original extracted project ZIP** with the script inside the `tools` folder, change `-File` to `".\tools\import_olist_sqlserver.ps1"` and run PowerShell from the `Track_A_Olist_Sales` folder.

Change `-DataFolder` to the actual CSV location and `-Server` to your SQL Server instance name, if different. The import tool uses Windows Authentication, skips tables that are already fully imported, and stops if it finds an incomplete import instead of deleting data.

Successful output ends with:

`ALL EIGHT TABLES IMPORTED AND COUNTS VERIFIED.`

### 3. Validate and run analysis

In SSMS, use the `OlistTrackA` database and run the scripts in this order:

1. `02_validation.sql`
2. `00_views.sql`
3. `03_analysis.sql`
4. `04_dashboard_exports.sql`

> `00_views.sql` must run before `03_analysis.sql`. The G3 query in `03_analysis.sql` is the optimized version used after the original query was slow.

### 4. Open the dashboard

Open `Track_A_Sales_Dashboard.xlsx` with Microsoft Excel and select the **Dashboard** worksheet.

- **Year dropdown:** cell `B4`
- **Month dropdown:** cell `E4`
- **Metrics:** Merchandise Sales, Delivered Orders, Average Order Value, and Sales per Calendar Day
- **Charts:** monthly sales, sales by weekday, sales by month-half, and order count by weekday

The workbook is a **SQL-derived snapshot**, not a live SQL Server connection. Changing year/month dropdowns recalculates the visuals from the workbook's stored data. To use different data, rerun the SQL exports, replace/refresh the source sheets, and reconcile the totals.

## Verified reference totals

For delivered orders purchased between **2017-01-01 and 2018-08-31**:

| Metric | Result |
| --- | ---: |
| Delivered orders | 96,211 |
| Merchandise sales (excluding freight) | BRL 13,181,027.13 |
| Average order value | BRL 137.00 |

Source CSVs contain 99,441 orders and 99,441 customer rows in total (before applying the analysis scope). The delivered-order totals above refer to the filtered historical analysis period.

## Business insights and recommendations

See `Track_A_Findings.pdf` for the full analysis. The dashboard can help stakeholders compare the same months across years, identify stronger weekdays and seasonal periods, and explore whether revenue changes are driven by order counts or average order value. Treat the findings as observational; the dataset does not establish campaign causality or profitability.

## Data notes

- Dates are filtered on purchase timestamp, not delivery timestamp.
- Merchandise sales exclude freight charges.
- Orders with multiple items are aggregated to **one order** before order-level metrics are computed, avoiding inflated counts.
- Comparisons between years use the comparable January–August period.
- Original Olist source and its license/terms should be reviewed before redistributing raw data.
