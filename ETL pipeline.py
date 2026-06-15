import pandas as pd
from sqlalchemy import create_engine
import os
import warnings
warnings.filterwarnings('ignore')

# ==========================================
# CẤU HÌNH ĐƯỜNG DẪN VÀ DATABASE
# ==========================================
# Lấy thư mục gốc chứa chính file script Python này làm căn cứ
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Đường dẫn tới thư mục chứa dữ liệu thô (Kaggle archive)
DATA_DIR = os.path.join(BASE_DIR, 'archive') 

# Đường dẫn tới thư mục BI để lưu file CSV sạch (Sẽ tự động tạo nếu chưa có)
BI_DIR = os.path.join(BASE_DIR, 'BI')
if not os.path.exists(BI_DIR):
    os.makedirs(BI_DIR)
    print(f"-> Đã tạo thư mục lưu trữ file sạch: {BI_DIR}")

# Thông tin kết nối PostgreSQL
DB_CONNECTION = 'postgresql://postgres:12345@localhost:5432/Data-warehouse-Ecommerce'

def read_csv(filename):
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file nguồn: {file_path}")
    return pd.read_csv(file_path)

print("1. ĐANG ĐỌC CÁC FILE CSV NGUỒN...")
df_customers = read_csv('olist_customers_dataset.csv')
df_products = read_csv('olist_products_dataset.csv')
df_orders = read_csv('olist_orders_dataset.csv')
df_items = read_csv('olist_order_items_dataset.csv')
df_translation = read_csv('product_category_name_translation.csv')

print("2. TRANSFORM: LÀM SẠCH VÀ ÁNH XẠ VÀO STAR SCHEMA...")

# --- DIM_CUSTOMER ---
df_dim_customer = df_customers[['customer_id', 'customer_unique_id', 'customer_city', 'customer_state']].copy()
df_dim_customer.rename(columns={
    'customer_id': 'id',
    'customer_unique_id': 'unique_id',
    'customer_city': 'city',
    'customer_state': 'state'
}, inplace=True)
df_dim_customer.drop_duplicates(subset=['id'], inplace=True)

# --- DIM_PRODUCT (Đã dịch danh mục sang Tiếng Anh) ---
df_products_translated = pd.merge(df_products, df_translation, on='product_category_name', how='left')
df_dim_product = df_products_translated[['product_id', 'product_category_name_english']].copy()
df_dim_product.rename(columns={
    'product_id': 'id',
    'product_category_name_english': 'category_name'
}, inplace=True)
df_dim_product['category_name'].fillna('Unknown', inplace=True)
df_dim_product.drop_duplicates(subset=['id'], inplace=True)

# --- CHUẨN BỊ TRANFORM CHO TIME VÀ FACT (Giữ date_key ở kiểu DATE) ---
df_orders['order_purchase_timestamp'] = pd.to_datetime(df_orders['order_purchase_timestamp'])

# SỬA TẠI ĐÂY: Dùng .dt.date để trả về kiểu DATE (YYYY-MM-DD) khớp với DB
df_orders['date_key'] = df_orders['order_purchase_timestamp'].dt.date
df_orders['hour'] = df_orders['order_purchase_timestamp'].dt.hour

# --- DIM_TIME (Giữ nguyên toàn bộ trạng thái để phân tích) ---
df_dim_time = df_orders[['date_key']].drop_duplicates().dropna().copy()
df_dim_time['date_key'] = pd.to_datetime(df_dim_time['date_key'])
df_dim_time['year'] = df_dim_time['date_key'].dt.year
df_dim_time['month'] = df_dim_time['date_key'].dt.month
df_dim_time['quarter'] = df_dim_time['date_key'].dt.quarter
df_dim_time['day_of_week'] = df_dim_time['date_key'].dt.dayofweek
df_dim_time['date_key'] = df_dim_time['date_key'].dt.date 

# --- FACT_ORDERS (Gồm cả price, freight_value và order_status) ---
df_fact = pd.merge(df_items, df_orders, on='order_id', how='inner')
df_fact_orders = df_fact[[
    'order_id', 'order_item_id', 'customer_id', 
    'product_id', 'date_key', 'hour', 'price', 'freight_value', 'order_status'
]].copy()
df_fact_orders.drop_duplicates(subset=['order_id', 'order_item_id'], inplace=True)


print("3. EXPORT: XUẤT 4 FILE CSV SẠCH VÀO THƯ MỤC BI (GHI ĐÈ FILE CŨ)...")
def save_to_bi_folder(df, filename):
    output_path = os.path.join(BI_DIR, filename)
    df.to_csv(output_path, index=False)
    print(f" V Đã lưu và thay thế file: {output_path}")

save_to_bi_folder(df_dim_customer, 'Dim_Customer_Clean.csv')
save_to_bi_folder(df_dim_product, 'Dim_Product_Clean.csv')
save_to_bi_folder(df_dim_time, 'Dim_Time_Clean.csv')
save_to_bi_folder(df_fact_orders, 'Fact_Orders_Clean.csv')


print("4. LOAD: NẠP DỮ LIỆU VÀO POSTGRESQL...")
engine = create_engine(DB_CONNECTION)

try:
    # Nạp 3 bảng Dimension trước (Tránh lỗi Foreign Key)
    df_dim_customer.to_sql('dim_customer', engine, if_exists='append', index=False)
    print(" V Tải vào DB thành công: dim_customer")
    
    df_dim_product.to_sql('dim_product', engine, if_exists='append', index=False)
    print(" V Tải vào DB thành công: dim_product")
    
    df_dim_time.to_sql('dim_time', engine, if_exists='append', index=False)
    print(" V Tải vào DB thành công: dim_time")
    
    # Nạp bảng Fact cuối cùng
    df_fact_orders.to_sql('fact_orders', engine, if_exists='append', index=False)
    print(" V Tải vào DB thành công: fact_orders")
    
    print("\n=> PIPELINE ETL HOÀN TẤT XỊN MỊN!")
except Exception as e:
    print(f"\n[LỖI] Trục trặc khi nạp data vào Database: {e}")