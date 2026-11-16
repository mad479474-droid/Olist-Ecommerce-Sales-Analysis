/* Track A | RUN SECOND AFTER IMPORT. Verify counts, keys, NULLs, join matches, dates, and money.
   Do not silently delete NULL-containing source rows. */
USE OlistTrackA;
GO
SELECT 'customers' AS table_name,COUNT_BIG(*) AS rows_found FROM dbo.customers UNION ALL
SELECT 'orders',COUNT_BIG(*) FROM dbo.orders UNION ALL
SELECT 'order_items',COUNT_BIG(*) FROM dbo.order_items UNION ALL
SELECT 'products',COUNT_BIG(*) FROM dbo.products UNION ALL
SELECT 'sellers',COUNT_BIG(*) FROM dbo.sellers UNION ALL
SELECT 'order_payments',COUNT_BIG(*) FROM dbo.order_payments UNION ALL
SELECT 'order_reviews',COUNT_BIG(*) FROM dbo.order_reviews UNION ALL
SELECT 'category_translation',COUNT_BIG(*) FROM dbo.category_translation;
-- Primary keys and item/payment sequence keys are enforced at table creation.
SELECT 'orders_without_customer' AS check_name, COUNT_BIG(*) AS affected_rows FROM dbo.orders o LEFT JOIN dbo.customers c ON c.customer_id=o.customer_id WHERE c.customer_id IS NULL
UNION ALL SELECT 'items_without_order',COUNT_BIG(*) FROM dbo.order_items i LEFT JOIN dbo.orders o ON o.order_id=i.order_id WHERE o.order_id IS NULL
UNION ALL SELECT 'delivered_without_items',COUNT_BIG(*) FROM dbo.orders o LEFT JOIN dbo.order_items i ON i.order_id=o.order_id WHERE o.order_status='delivered' AND o.order_purchase_timestamp>='20170101' AND o.order_purchase_timestamp<'20180901' AND i.order_id IS NULL
UNION ALL SELECT 'review_rows_invalid_score',COUNT_BIG(*) FROM dbo.order_reviews WHERE review_score NOT BETWEEN 1 AND 5 OR review_score IS NULL
UNION ALL SELECT 'negative_item_price',COUNT_BIG(*) FROM dbo.order_items WHERE price<0
UNION ALL SELECT 'negative_freight',COUNT_BIG(*) FROM dbo.order_items WHERE freight_value<0;
SELECT MIN(order_purchase_timestamp) AS first_purchase,MAX(order_purchase_timestamp) AS last_purchase FROM dbo.orders;
SELECT COUNT(*) AS review_orders_with_multiple_rows FROM (SELECT order_id FROM dbo.order_reviews GROUP BY order_id HAVING COUNT(*)>1) t;
SELECT order_status,COUNT_BIG(*) AS all_orders_in_scope FROM dbo.orders WHERE order_purchase_timestamp>='20170101' AND order_purchase_timestamp<'20180901' GROUP BY order_status ORDER BY all_orders_in_scope DESC;
GO
