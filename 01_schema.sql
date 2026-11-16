/* Track A | SQL Server 2022 | RUN FIRST
  Create database and eight original Olist tables. Import original CSVs unmodified.
  These tables preserve original CSV columns; source_review_row_index is generated locally.
*/
IF DB_ID(N'OlistTrackA') IS NULL CREATE DATABASE OlistTrackA;
GO
USE OlistTrackA;
GO
CREATE TABLE dbo.customers (
 customer_id VARCHAR(32) NOT NULL PRIMARY KEY,
 customer_unique_id VARCHAR(32), customer_zip_code_prefix VARCHAR(10),
 customer_city NVARCHAR(150), customer_state VARCHAR(2));
CREATE TABLE dbo.orders (
 order_id VARCHAR(32) NOT NULL PRIMARY KEY,
 customer_id VARCHAR(32), order_status VARCHAR(24),
 order_purchase_timestamp DATETIME2(0), order_approved_at DATETIME2(0) NULL,
 order_delivered_carrier_date DATETIME2(0) NULL,
 order_delivered_customer_date DATETIME2(0) NULL,
 order_estimated_delivery_date DATETIME2(0) NULL);
CREATE TABLE dbo.order_items (
 order_id VARCHAR(32) NOT NULL, order_item_id INT NOT NULL,
 product_id VARCHAR(32), seller_id VARCHAR(32), shipping_limit_date DATETIME2(0),
 price DECIMAL(18,2), freight_value DECIMAL(18,2),
 CONSTRAINT PK_order_items PRIMARY KEY (order_id,order_item_id));
CREATE TABLE dbo.products (
 product_id VARCHAR(32) NOT NULL PRIMARY KEY, product_category_name NVARCHAR(150),
 product_name_lenght INT NULL, product_description_lenght INT NULL,
 product_photos_qty INT NULL, product_weight_g INT NULL,
 product_length_cm INT NULL, product_height_cm INT NULL, product_width_cm INT NULL);
CREATE TABLE dbo.sellers (
 seller_id VARCHAR(32) NOT NULL PRIMARY KEY, seller_zip_code_prefix VARCHAR(10),
 seller_city NVARCHAR(150), seller_state VARCHAR(2));
CREATE TABLE dbo.order_payments (
 order_id VARCHAR(32) NOT NULL, payment_sequential INT NOT NULL,
 payment_type VARCHAR(30), payment_installments INT, payment_value DECIMAL(18,2),
 CONSTRAINT PK_payments PRIMARY KEY (order_id,payment_sequential));
CREATE TABLE dbo.order_reviews (
 source_review_row_index BIGINT IDENTITY(1,1) NOT NULL PRIMARY KEY,
 review_id VARCHAR(32), order_id VARCHAR(32), review_score INT,
 review_comment_title NVARCHAR(4000), review_comment_message NVARCHAR(MAX),
 review_creation_date DATETIME2(0) NULL, review_answer_timestamp DATETIME2(0) NULL);
CREATE TABLE dbo.category_translation (
 product_category_name NVARCHAR(150) NOT NULL PRIMARY KEY,
 product_category_name_english NVARCHAR(150));
GO
-- Import instructions: see docs/IMPORT_SQL_SERVER.md. Import CSVs using ordered column mapping.
-- Do NOT add foreign keys until validation checks have been reviewed.
CREATE INDEX IX_orders_purchase ON dbo.orders(order_purchase_timestamp,order_status) INCLUDE(customer_id);
CREATE INDEX IX_items_product ON dbo.order_items(product_id);
CREATE INDEX IX_reviews_order ON dbo.order_reviews(order_id);
CREATE INDEX IX_payments_order ON dbo.order_payments(order_id);
GO
