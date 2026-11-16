/* Track A | RUN FOURTH | SQL Server 2022
 All results follow 2017-01-01 inclusive through 2018-09-01 exclusive, purchased-date basis.
 Merchandise sales SUM(price) on delivered orders, EXCLUDING freight.
 Rates preserve denominators, with NULL for a zero denominator.
 Some IDs require multiple SELECT statements to show supporting evidence.
 Run 00_views.sql before this file.
*/
USE OlistTrackA;
GO
/* G1 | Order status: output one row per status; scalar subquery overall denominator. */
SELECT order_status,COUNT_BIG(*) AS order_count,
 CAST(100.0*COUNT_BIG(*)/NULLIF((SELECT COUNT_BIG(*) FROM dbo.v_orders_scope),0) AS DECIMAL(12,2)) AS pct_of_all_orders
FROM dbo.v_orders_scope GROUP BY order_status ORDER BY order_count DESC,order_status;
SELECT COUNT_BIG(*) AS delivered_orders,COUNT(DISTINCT customer_unique_id) AS unique_customers,
 SUM(merchandise_sales_brl) AS merchandise_sales_brl,
 CAST(SUM(merchandise_sales_brl)/NULLIF(COUNT_BIG(*),0) AS DECIMAL(18,2)) AS aov_brl,
 SUM(CASE WHEN item_rows IS NULL THEN 1 ELSE 0 END) AS missing_item_orders
FROM dbo.v_delivered;
GO
/* G2 | Monthly trend incl zero months; stages CTE; LAG, SUM OVER cumulative. Grain month. */
WITH months AS (
 SELECT CAST('20170101' AS DATE) AS month_start
 UNION ALL SELECT DATEADD(MONTH,1,month_start) FROM months WHERE month_start<'20180801'
), monthly AS (
 SELECT m.month_start, COUNT(d.order_id) AS delivered_orders,
 COALESCE(SUM(d.merchandise_sales_brl),0) AS sales_brl
 FROM months m LEFT JOIN dbo.v_delivered d ON d.purchase_month=m.month_start
 GROUP BY m.month_start
), compare AS (
 SELECT *,LAG(sales_brl) OVER(ORDER BY month_start) AS previous_sales_brl,
 SUM(sales_brl) OVER(ORDER BY month_start ROWS UNBOUNDED PRECEDING) AS running_sales_brl
 FROM monthly
)
SELECT CONVERT(CHAR(7),month_start,126) AS purchase_month,delivered_orders,sales_brl,
 CAST(sales_brl/NULLIF(delivered_orders,0) AS DECIMAL(18,2)) AS aov_brl,
 CAST(100.0*(sales_brl-previous_sales_brl)/NULLIF(previous_sales_brl,0) AS DECIMAL(12,2)) AS growth_pct,
 running_sales_brl
FROM compare ORDER BY month_start OPTION (MAXRECURSION 0);
GO

    /* G3 - Review and Payment Coverage (Optimized) */

    WITH delivered_orders AS (
        SELECT
            order_id,
            DATEFROMPARTS(
                YEAR(order_purchase_timestamp),
                MONTH(order_purchase_timestamp), 1
            ) AS purchase_month
        FROM dbo.orders
        WHERE order_status = 'delivered'
          AND order_purchase_timestamp >= '20170101'
          AND order_purchase_timestamp < '20180901'
    ),
    review_check AS (
        SELECT DISTINCT order_id
        FROM dbo.order_reviews
        WHERE review_score BETWEEN 1 AND 5
    ),
    payment_check AS (
        SELECT order_id
        FROM dbo.order_payments
        GROUP BY order_id
    ),
    coverage AS (
        SELECT
            d.order_id,
            d.purchase_month,
            CASE WHEN r.order_id IS NULL THEN 0 ELSE 1 END AS has_review,
            CASE WHEN p.order_id IS NULL THEN 0 ELSE 1 END AS has_payment
        FROM delivered_orders d
        LEFT JOIN review_check r ON d.order_id = r.order_id
        LEFT JOIN payment_check p ON d.order_id = p.order_id
    )
    SELECT
        CONVERT(CHAR(7), purchase_month, 126) AS purchase_month,
        COUNT(*) AS delivered_orders,
        SUM(has_review) AS with_review,
        COUNT(*) - SUM(has_review) AS missing_review,
        CAST(100.0 * SUM(has_review) / NULLIF(COUNT(*), 0)
             AS DECIMAL(12,2)) AS review_coverage_pct,
        SUM(has_payment) AS with_payment,
        COUNT(*) - SUM(has_payment) AS missing_payment,
        CAST(100.0 * SUM(has_payment) / NULLIF(COUNT(*), 0)
             AS DECIMAL(12,2)) AS payment_coverage_pct
    FROM coverage
    GROUP BY purchase_month
    ORDER BY purchase_month;

    SELECT TOP (30)
        o.order_id,
        CONVERT(CHAR(7), o.order_purchase_timestamp, 126) AS purchase_month,
        CASE WHEN NOT EXISTS (
            SELECT 1 FROM dbo.order_reviews r
            WHERE r.order_id = o.order_id
              AND r.review_score BETWEEN 1 AND 5
        ) THEN 1 ELSE 0 END AS missing_review,
        CASE WHEN NOT EXISTS (
            SELECT 1 FROM dbo.order_payments p
            WHERE p.order_id = o.order_id
        ) THEN 1 ELSE 0 END AS missing_payment
    FROM dbo.orders o
    WHERE o.order_status = 'delivered'
      AND o.order_purchase_timestamp >= '20170101'
      AND o.order_purchase_timestamp < '20180901'
      AND (
          NOT EXISTS (
              SELECT 1 FROM dbo.order_reviews r
              WHERE r.order_id = o.order_id
                AND r.review_score BETWEEN 1 AND 5
          )
          OR NOT EXISTS (
              SELECT 1 FROM dbo.order_payments p
              WHERE p.order_id = o.order_id
          )
      )
    ORDER BY o.order_purchase_timestamp, o.order_id;

GO
/* A1 | Jan-Aug both years; grain year; comparable months. */
WITH y AS (SELECT YEAR(purchase_date) AS y,COUNT_BIG(*) AS orders,SUM(merchandise_sales_brl) AS sales
 FROM dbo.v_delivered WHERE MONTH(purchase_date)<=8 GROUP BY YEAR(purchase_date)),
p AS (SELECT *,LAG(sales) OVER(ORDER BY y) AS prior_sales,
 LAG(orders) OVER(ORDER BY y) AS prior_orders FROM y)
SELECT y,orders,sales,CAST(sales/NULLIF(orders,0) AS DECIMAL(18,2)) AS aov_brl,
 CAST(100.0*(sales-prior_sales)/NULLIF(prior_sales,0) AS DECIMAL(12,2)) AS sales_yoy_growth_pct,
 CAST(100.0*(orders-prior_orders)/NULLIF(prior_orders,0) AS DECIMAL(12,2)) AS orders_yoy_growth_pct
FROM p ORDER BY y;
GO
/* A2 | All dates, zero-sales dates included. WEEKDAY language independent: 1900-01-01 is Monday.
 Grain weekday. Use a complete date spine and calendar-day denominator. */
WITH days AS (
 SELECT CAST('20170101' AS DATE) dt UNION ALL
 SELECT DATEADD(DAY,1,dt) FROM days WHERE dt<'20180831'
), ds AS (
 SELECT days.dt,(DATEDIFF(DAY,'19000101',days.dt)%7+7)%7 AS weekday_no,
 COUNT(d.order_id) AS orders,COALESCE(SUM(d.merchandise_sales_brl),0) AS sales
 FROM days LEFT JOIN dbo.v_delivered d ON d.purchase_date=days.dt GROUP BY days.dt
)
SELECT weekday_no,CHOOSE(weekday_no+1,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') AS weekday_name,
 COUNT_BIG(*) AS calendar_days,SUM(orders) AS delivered_orders,SUM(sales) AS sales_brl,
 CAST(SUM(sales)/NULLIF(SUM(orders),0) AS DECIMAL(18,2)) AS aov_brl,
 CAST(1.0*SUM(orders)/NULLIF(COUNT_BIG(*),0) AS DECIMAL(18,3)) AS orders_per_calendar_day,
 CAST(SUM(sales)/NULLIF(COUNT_BIG(*),0) AS DECIMAL(18,2)) AS sales_per_calendar_day
FROM ds GROUP BY weekday_no ORDER BY weekday_no OPTION (MAXRECURSION 0);
GO
/* A3 | Correlated subquery: daily sales > avg calendar day in its purchase month (zeros included). Grain qualifying date. */
WITH dates AS (SELECT CAST('20170101' AS DATE) dt UNION ALL SELECT DATEADD(DAY,1,dt) FROM dates WHERE dt<'20180831'),
 daily AS (SELECT dates.dt,DATEFROMPARTS(YEAR(dates.dt),MONTH(dates.dt),1) mn,
 COALESCE(SUM(d.merchandise_sales_brl),0) sales_brl FROM dates
 LEFT JOIN dbo.v_delivered d ON d.purchase_date=dates.dt GROUP BY dates.dt),
 compared AS (SELECT a.dt,a.mn,a.sales_brl,
 (SELECT AVG(CAST(b.sales_brl AS DECIMAL(24,4))) FROM daily b WHERE b.mn=a.mn) AS monthly_calendar_daily_mean
 FROM daily a)
SELECT dt,CONVERT(CHAR(7),mn,126) AS purchase_month,sales_brl,monthly_calendar_daily_mean,
 sales_brl-monthly_calendar_daily_mean AS difference_brl
FROM compared WHERE sales_brl>monthly_calendar_daily_mean ORDER BY difference_brl DESC,dt OPTION (MAXRECURSION 0);
GO
/* A4 | Multi-row IN subquery chooses top-three months; item-level category attribution. Grain month-category. */
WITH monthly AS (SELECT TOP (3) purchase_month,SUM(merchandise_sales_brl) AS sales FROM dbo.v_delivered
 GROUP BY purchase_month ORDER BY sales DESC,purchase_month),
 itemcats AS (
 SELECT d.purchase_month,COALESCE(t.product_category_name_english,p.product_category_name,N'Uncategorized') AS category,
 i.price FROM dbo.v_delivered d JOIN dbo.order_items i ON i.order_id=d.order_id
 LEFT JOIN dbo.products p ON p.product_id=i.product_id
 LEFT JOIN dbo.category_translation t ON t.product_category_name=p.product_category_name
 WHERE d.purchase_month IN (SELECT purchase_month FROM monthly)
), results AS (
 SELECT purchase_month,category,SUM(price) AS category_sales_brl,COUNT_BIG(*) AS items
 FROM itemcats GROUP BY purchase_month,category
)
SELECT CONVERT(CHAR(7),purchase_month,126) AS purchase_month,category,category_sales_brl,items,
 CAST(100.0*category_sales_brl/NULLIF(SUM(category_sales_brl) OVER(PARTITION BY purchase_month),0) AS DECIMAL(12,3)) AS month_sales_share_pct,
 DENSE_RANK() OVER(PARTITION BY purchase_month ORDER BY category_sales_brl DESC) AS category_rank
FROM results ORDER BY purchase_month,category_rank,category;
GO
/* A5 | all statuses; not historical status changes, only observed final snapshot; month grain. */
SELECT CONVERT(CHAR(7),purchase_month,126) AS purchase_month,COUNT_BIG(*) AS all_orders,
 SUM(CASE WHEN order_status='delivered' THEN 1 ELSE 0 END) AS delivered,
 SUM(CASE WHEN order_status='canceled' THEN 1 ELSE 0 END) AS canceled,
 SUM(CASE WHEN order_status NOT IN ('delivered','canceled') THEN 1 ELSE 0 END) AS other,
 CAST(100.0*SUM(CASE WHEN order_status='delivered' THEN 1 ELSE 0 END)/NULLIF(COUNT_BIG(*),0) AS DECIMAL(12,2)) AS delivered_pct,
 CAST(100.0*SUM(CASE WHEN order_status='canceled' THEN 1 ELSE 0 END)/NULLIF(COUNT_BIG(*),0) AS DECIMAL(12,2)) AS canceled_pct
FROM dbo.v_orders_scope GROUP BY purchase_month ORDER BY purchase_month;
GO
/* A6 | self join of date spine on 7 days earlier, all zero-sales dates preserved. Grain date. */
WITH days AS (SELECT CAST('20170101' AS DATE) dt UNION ALL SELECT DATEADD(DAY,1,dt) FROM days WHERE dt<'20180831'),
 daily AS (SELECT days.dt,COALESCE(SUM(d.merchandise_sales_brl),0) sales_brl
 FROM days LEFT JOIN dbo.v_delivered d ON d.purchase_date=days.dt GROUP BY days.dt)
SELECT a.dt,a.sales_brl,b.sales_brl AS sales_7days_earlier_brl,
 a.sales_brl-b.sales_brl AS change_brl,
 CAST(100.0*(a.sales_brl-b.sales_brl)/NULLIF(b.sales_brl,0) AS DECIMAL(12,2)) AS change_pct,
 CASE WHEN b.dt IS NULL THEN 'No prior date in scope' WHEN b.sales_brl=0 THEN 'Zero prior sales' ELSE 'Comparable' END AS comparison_flag
FROM daily a LEFT JOIN daily b ON b.dt=DATEADD(DAY,-7,a.dt)
ORDER BY a.dt OPTION (MAXRECURSION 0);
GO
/* A7 | first 1-15 and 16-end; use actual calendar day lengths; grain month/half. */
WITH months AS (SELECT CAST('20170101' AS DATE) mn UNION ALL SELECT DATEADD(MONTH,1,mn) FROM months WHERE mn<'20180801'),
 halves AS (SELECT m.mn,x.half_no,
 CASE WHEN x.half_no=1 THEN 15 ELSE DAY(EOMONTH(m.mn))-15 END AS n_calendar_days
 FROM months m CROSS JOIN (VALUES (1),(2)) x(half_no)),
 summaries AS (
 SELECT h.mn,h.half_no,h.n_calendar_days,COUNT(d.order_id) AS orders,COALESCE(SUM(d.merchandise_sales_brl),0) sales_brl
 FROM halves h LEFT JOIN dbo.v_delivered d ON d.purchase_month=h.mn
 AND (CASE WHEN DAY(d.purchase_date)<=15 THEN 1 ELSE 2 END)=h.half_no
 GROUP BY h.mn,h.half_no,h.n_calendar_days)
SELECT CONVERT(CHAR(7),mn,126) AS purchase_month,
 CASE half_no WHEN 1 THEN 'Days 01-15' ELSE 'Days 16-end' END AS period,n_calendar_days,orders,sales_brl,
 CAST(sales_brl/NULLIF(n_calendar_days,0) AS DECIMAL(18,2)) AS sales_per_day_brl,
 CAST(1.0*orders/NULLIF(n_calendar_days,0) AS DECIMAL(18,3)) AS orders_per_day,
 CAST(sales_brl/NULLIF(orders,0) AS DECIMAL(18,2)) AS aov_brl
FROM summaries ORDER BY mn,half_no OPTION (MAXRECURSION 0);
GO
/* O1 | Team question: Which quarters have the largest intra-quarter monthly sales range?
   Business use: capacity planning; measure calendar-month sales variability.
   For incomplete Q3-2018, explicitly disclose only Jul-Aug, not Sep.
   Grain year-quarter, output count/sum/mean/min/max/range. */
WITH monthly AS (
 SELECT YEAR(purchase_month) yy,DATEPART(QUARTER,purchase_month) qq,purchase_month,
 SUM(merchandise_sales_brl) monthly_sales FROM dbo.v_delivered GROUP BY purchase_month
)
SELECT yy,qq,COUNT_BIG(*) AS observed_months,SUM(monthly_sales) AS sales_brl,
 AVG(monthly_sales) AS mean_monthly_sales_brl,MIN(monthly_sales) AS min_month_sales_brl,
 MAX(monthly_sales) AS max_month_sales_brl,MAX(monthly_sales)-MIN(monthly_sales) AS monthly_range_brl
FROM monthly GROUP BY yy,qq ORDER BY yy,qq;
GO
/* O2 | Team question: Do weekday and weekend daily sales differ after normalizing for calendar days?
   Business use: staffing. Weekend = Sat/Sun. Grain weekday/weekend, keep calendar-day denominator. */
WITH days AS (SELECT CAST('20170101' AS DATE) dt UNION ALL SELECT DATEADD(DAY,1,dt) FROM days WHERE dt<'20180831'),
 daily AS (SELECT days.dt,CASE WHEN DATEDIFF(DAY,'19000101',days.dt)%7 IN (5,6) THEN 'Weekend' ELSE 'Weekdays' END AS day_type,
 COUNT(d.order_id) AS orders,COALESCE(SUM(d.merchandise_sales_brl),0) sales_brl
 FROM days LEFT JOIN dbo.v_delivered d ON d.purchase_date=days.dt GROUP BY days.dt)
SELECT day_type,COUNT_BIG(*) AS calendar_days,SUM(orders) AS delivered_orders,SUM(sales_brl) AS sales_brl,
 CAST(SUM(sales_brl)/NULLIF(COUNT_BIG(*),0) AS DECIMAL(18,2)) AS sales_per_day_brl,
 CAST(1.0*SUM(orders)/NULLIF(COUNT_BIG(*),0) AS DECIMAL(18,3)) AS orders_per_day,
 CAST(SUM(sales_brl)/NULLIF(SUM(orders),0) AS DECIMAL(18,2)) AS aov_brl
FROM daily GROUP BY day_type ORDER BY day_type OPTION (MAXRECURSION 0);
GO
