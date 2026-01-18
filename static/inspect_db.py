import mysql.connector

# DIRECT DB CONFIG (no imports)
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "property_db"
}

db = mysql.connector.connect(**DB_CONFIG)
cursor = db.cursor(dictionary=True)

print("\n========== DATABASE STRUCTURE ==========\n")

cursor.execute("SHOW TABLES")
tables = cursor.fetchall()

for t in tables:
    table_name = list(t.values())[0]
    print(f"\n--- TABLE: {table_name} ---")

    cursor.execute(f"DESCRIBE {table_name}")
    cols = cursor.fetchall()

    for c in cols:
        print(
            f"Column: {c['Field']:<25} "
            f"Type: {c['Type']:<18} "
            f"Null: {c['Null']:<5} "
            f"Key: {c['Key']}"
        )

cursor.close()
db.close()
