/* Track A | RUN THIRD. Order-grain views prevent payment x item x review duplication. */
USE OlistTrackA;
GO
CREATE OR ALTER VIEW dbo.v_order_items_total AS
 SELECT order_id,COUNT_BIG(*) AS item_rows, SUM(price) AS merchandise_sales_brl, SUM(freight_value) AS freight_brl
 FROM dbo.order_items GROUP BY order_id;
GO
CREATE OR ALTER VIEW dbo.v_order_payments_total AS
 SELECT order_id,COUNT_BIG(*) AS payment_records,SUM(payment_value) AS payment_total_brl
 FROM dbo.order_payments GROUP BY order_id;
GO
CREATE OR ALTER VIEW dbo.v_analysis_review AS
 SELECT order_id,review_score,review_id,source_review_row_index FROM (
   SELECT r.*,ROW_NUMBER() OVER(PARTITION BY order_id ORDER BY
     CASE WHEN review_answer_timestamp IS NOT NULL THEN 1 ELSE 0 END DESC,
     review_answer_timestamp DESC,review_creation_date DESC,review_id DESC,source_review_row_index DESC) AS rn
   FROM dbo.order_reviews r WHERE review_score BETWEEN 1 AND 5
 ) z WHERE rn=1;
GO
CREATE OR ALTER VIEW dbo.v_orders_scope AS
 SELECT o.*,c.customer_unique_id,it.item_rows,it.merchandise_sales_brl,it.freight_brl,
       pay.payment_records,pay.payment_total_brl,r.review_score,
       CAST(o.order_purchase_timestamp AS DATE) AS purchase_date,
       DATEFROMPARTS(YEAR(o.order_purchase_timestamp),MONTH(o.order_purchase_timestamp),1) AS purchase_month
 FROM dbo.orders o
 LEFT JOIN dbo.customers c ON c.customer_id=o.customer_id
 LEFT JOIN dbo.v_order_items_total it ON it.order_id=o.order_id
 LEFT JOIN dbo.v_order_payments_total pay ON pay.order_id=o.order_id
 LEFT JOIN dbo.v_analysis_review r ON r.order_id=o.order_id
 WHERE o.order_purchase_timestamp>='20170101' AND o.order_purchase_timestamp<'20180901';
GO
CREATE OR ALTER VIEW dbo.v_delivered AS
 SELECT * FROM dbo.v_orders_scope WHERE order_status='delivered';
GO
