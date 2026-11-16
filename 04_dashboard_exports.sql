/* Track A: dashboard inputs, run AFTER 00_views.sql. Export each result to CSV with header.
   Dashboard_daily: one row per calendar date. Filter-safe year/month/weekday/half; all joins already resolved in SQL.
   KPIs: SUM(sales_brl), SUM(orders), SUM(sales)/SUM(orders), YoY Jan-Aug equal months.
*/
USE OlistTrackA;
GO
WITH days AS (
 SELECT CAST('20170101' AS DATE) dt
 UNION ALL SELECT DATEADD(DAY,1,dt) FROM days WHERE dt<'20180831'
)
SELECT days.dt AS purchase_date,YEAR(days.dt) AS purchase_year,MONTH(days.dt) AS purchase_month_no,
 CHOOSE(1+((DATEDIFF(DAY,'19000101',days.dt)%7+7)%7),
 'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') AS weekday,
 CAST(1 AS INT) AS calendar_days,COUNT(d.order_id) AS delivered_orders,
 COALESCE(SUM(d.merchandise_sales_brl),0) AS sales_brl,
 CASE WHEN DAY(days.dt)<=15 THEN 1 ELSE 2 END AS month_half
FROM days LEFT JOIN dbo.v_delivered d ON d.purchase_date=days.dt
GROUP BY days.dt ORDER BY days.dt OPTION (MAXRECURSION 0);
GO
-- Monthly export: one row per month (no duplicate order counts across groups).
WITH months AS (SELECT CAST('20170101' AS DATE) dt UNION ALL SELECT DATEADD(MONTH,1,dt) FROM months WHERE dt<'20180801')
SELECT YEAR(m.dt) AS year_no,MONTH(m.dt) AS month_no,CONVERT(CHAR(7),m.dt,126) AS purchase_month,
 COUNT(d.order_id) AS delivered_orders,COALESCE(SUM(d.merchandise_sales_brl),0) AS sales_brl
FROM months m LEFT JOIN dbo.v_delivered d ON d.purchase_month=m.dt GROUP BY m.dt
ORDER BY m.dt OPTION (MAXRECURSION 0);
GO
