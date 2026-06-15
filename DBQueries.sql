-- 1. TẠO CÁC BẢNG DIMENSION TRƯỚC

-- Tạo bảng Dim_Customer
CREATE TABLE Dim_Customer (
    id VARCHAR(50) PRIMARY KEY,
    unique_id VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(20)
);

-- Tạo bảng Dim_Product
CREATE TABLE Dim_Product (
    id VARCHAR(50) PRIMARY KEY,
    category_name VARCHAR(100)
);

-- Tạo bảng Dim_Time
-- Lưu ý: Đổi tên cột 'Date' thành 'date_key' để tránh trùng với từ khóa DATE trong SQL
CREATE TABLE Dim_Time (
    date_key DATE PRIMARY KEY,
    year INTEGER,
    month INTEGER,
    quarter INTEGER,
    day_of_week INTEGER
);

-- 2. TẠO BẢNG FACT SAU CÙNG

-- Tạo bảng Fact_Orders (Bản vá lỗi chuẩn xác)
CREATE TABLE Fact_Orders (
    order_id VARCHAR(50), 
    order_item_id INTEGER, -- Thêm cột này làm một phần của khóa chính
    customer_id VARCHAR(50),
    product_id VARCHAR(50),
    date_key DATE,
    price NUMERIC(10,2), 
    freight_value NUMERIC(10,2), 
    
    -- THIẾT LẬP KHÓA CHÍNH PHỨC HỢP
    CONSTRAINT pk_fact_orders 
        PRIMARY KEY (order_id, order_item_id),
    
    -- Thiết lập các khóa ngoại (Foreign Keys)
    CONSTRAINT fk_customer
        FOREIGN KEY(customer_id) 
        REFERENCES Dim_Customer(id),
        
    CONSTRAINT fk_product
        FOREIGN KEY(product_id) 
        REFERENCES Dim_Product(id),
        
    CONSTRAINT fk_date
        FOREIGN KEY(date_key) 
        REFERENCES Dim_Time(date_key)
);

SELECT * FROM public.dim_customer
select * from dim_product
select * from dim

