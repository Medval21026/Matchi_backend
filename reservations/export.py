import pymysql
import csv
import os

# Database connection
conn = pymysql.connect(
    host="medlzd.mysql.pythonanywhere-services.com",
    user="medlzd",
    password="matchimatchi",
    database="medlzd$matchi"
)

cursor = conn.cursor()

# Get all table names
cursor.execute("SHOW TABLES")
tables = [table[0] for table in cursor.fetchall()]

# Ensure directory exists for storing CSV files
export_dir = "/"
os.makedirs(export_dir, exist_ok=True)

# Loop through each table and export to CSV
for table in tables:
    file_path = os.path.join(export_dir, f"{table}.csv")

    cursor.execute(f"SELECT * FROM {table}")
    columns = [desc[0] for desc in cursor.description]

    with open(file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(columns)  # Write column headers
        writer.writerows(cursor.fetchall())  # Write data

    print(f"Exported {table} to {file_path}")

conn.close()
print("All tables exported successfully!")
