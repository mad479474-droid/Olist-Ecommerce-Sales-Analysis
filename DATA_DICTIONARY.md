# Olist Track A — Data Dictionary

All source tables are kept as separate entities. Scope: purchase timestamps [2017-01-01, 2018-09-01); source data outside the window remains stored. Order metrics refer to **delivered** orders unless noted.

| Table | Grain / key | Relevant fields / business meaning |
|---|---|---|
| customers | One order-associated customer record; PK `customer_id` | `customer_unique_id` identifies a real repeated buyer, `customer_city`, `customer_state`, `customer_zip_code_prefix` text |
| orders | One order; PK `order_id` | `customer_id` joins customers; `order_status` snapshot, `order_purchase_timestamp` purchase-date scope, approval/carrier/customer/estimated-delivery dates nullable |
| order_items | One item row in order; composite PK (`order_id`, `order_item_id`) | `product_id`, `seller_id`, `price` BRL merchandise value, `freight_value` BRL, `shipping_limit_date`. Count rows; do **not** sum sequence `order_item_id` |
| products | One product; PK `product_id` | Category name, dimensions, weight; `product_name_lenght` and `product_description_lenght` retain source's original spelling |
| sellers | One seller; PK `seller_id` | Seller location state/city |
| order_payments | One payment record; PK (`order_id`, `payment_sequential`) | `payment_type`, `payment_installments` (not record count), `payment_value` BRL |
| order_reviews | One source review row; generated `source_review_row_index` for tie-breaks | `review_id` not globally assumed unique, `order_id`, score 1–5, comment text, review dates. One valid review selected per order by latest answer/creation date and tie-breaks |
| category_translation | One category mapping; PK `product_category_name` | English category name, LEFT JOIN preserves missing translations |

## Analytical views / metrics

| View or field | Grain | Meaning |
|---|---|---|
| `v_order_items_total` | order_id | `merchandise_sales_brl=SUM(price)` (excludes freight), `freight_brl=SUM(freight_value)`, `item_rows=COUNT(*)` |
| `v_order_payments_total` | order_id | `payment_records=COUNT(*)`, `payment_total_brl=SUM(payment_value)` |
| `v_analysis_review` | order_id | Latest selected valid review, nullable if no valid review |
| `v_orders_scope` | order_id | Original orders in window plus all order-grain derived measures, no order multiplication |
| `v_delivered` | order_id | Delivered orders within scope |
| `purchase_date` | order | CAST purchase timestamp AS DATE |
| `purchase_month` | order | First day of purchase month |
| `AOV` | selected delivered orders | SUM merchandise sales / count distinct delivered order IDs; exclude freight |
| `growth_pct` | successive months | 100*(current-previous)/previous; NULL if no/zero prior month |
| `orders_per_day` | weekday or half month | delivered order count divided by **all calendar days** of the group, including zero-sales days |
| `sales_per_day_brl` | weekday or half month | total merchandise sales divided by calendar days |
| `review_coverage_pct` | delivered orders | 100*valid reviewed orders / delivered orders; no valid review is not rating zero |
| `status_pct` | all orders | 100*status order count / count of all statuses in purchase window |

**Units**: BRL for all sales/currency fields, calendar days for time denominators, percentage for `%`, counts for orders/items. Row grain matters: item rows are one-to-many relative to orders; never join payments to items and sum the resulting rows.
