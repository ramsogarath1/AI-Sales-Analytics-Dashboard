"""
Test Datasets Generator Script for Phase 2 Verification.
Generates valid, empty, malformed, unsupported, and missing-column test files.
"""

import os
import pandas as pd

TEST_DIR = os.path.join(os.path.dirname(__file__), "test_datasets")
os.makedirs(TEST_DIR, exist_ok=True)

# 1. Valid Sales Data (CSV & XLSX)
valid_data = {
    "Order ID": ["ORD-1001", "ORD-1002", "ORD-1003", "ORD-1004", "ORD-1005", "ORD-1005"], # 1 duplicate row
    "Order Date": ["2025-01-15", "2025-01-16", "01/17/2025", "2025-01-18", "2025-01-19", "2025-01-19"],
    "Customer ID": ["CUST-01", "CUST-02", "CUST-03", "CUST-01", "CUST-04", "CUST-04"],
    "Customer Name": [" Alice Smith ", "Bob Jones", "Charlie Brown", "Alice Smith", "David Miller", "David Miller"],
    "Product Name": ["Wireless Mouse", "Mechanical Keyboard", "USB-C Hub", "27-inch Monitor", "Ergonomic Chair", "Ergonomic Chair"],
    "Category": ["Electronics", "Electronics", "Electronics", "Hardware", "Furniture", "Furniture"],
    "Region": ["North", "South", "East", "West", "North", "North"],
    "Quantity": [2, 1, 3, 1, 2, 2],
    "Sales Amount": ["$50.00 ", "$120.00", "$45.50", "$300.00", "$400.00", "$400.00"],
    "Profit": ["$15.00", "$35.00", "$10.00", "$80.00", "$95.00", "$95.00"]
}

df_valid = pd.DataFrame(valid_data)

# Save valid CSV
valid_csv_path = os.path.join(TEST_DIR, "valid_sales_data.csv")
df_valid.to_csv(valid_csv_path, index=False)

# Save valid XLSX
valid_xlsx_path = os.path.join(TEST_DIR, "valid_sales_data.xlsx")
df_valid.to_excel(valid_xlsx_path, index=False, engine="openpyxl")

# 2. Empty CSV File
empty_csv_path = os.path.join(TEST_DIR, "empty_file.csv")
with open(empty_csv_path, "w") as f:
    f.write("")

# 3. Malformed File (unparseable binary junk inside .csv)
malformed_csv_path = os.path.join(TEST_DIR, "malformed_file.csv")
with open(malformed_csv_path, "wb") as f:
    f.write(bytes([0x80, 0x81, 0x82, 0xFF, 0xFE, 0xFD]))

# 4. Unsupported File Type
unsupported_txt_path = os.path.join(TEST_DIR, "unsupported_file.txt")
with open(unsupported_txt_path, "w") as f:
    f.write("This is a plain text document, not a CSV or Excel file.")

# 5. Missing Expected Sales Columns (no dates, no revenue, no order_id)
missing_cols_data = {
    "Employee Name": ["John", "Sarah", "Mike"],
    "Department": ["HR", "IT", "Finance"],
    "Hire Year": [2018, 2020, 2021]
}
df_missing = pd.DataFrame(missing_cols_data)
missing_csv_path = os.path.join(TEST_DIR, "missing_columns.csv")
df_missing.to_csv(missing_csv_path, index=False)

print("[SUCCESS] Test datasets successfully created in:", TEST_DIR)
