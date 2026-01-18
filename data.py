import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root"
)

cur = conn.cursor()

# Create database
cur.execute("CREATE DATABASE IF NOT EXISTS tanvidb")
cur.execute("USE tanvidb")

# ================= PROPERTIES =================
cur.execute("""
CREATE TABLE IF NOT EXISTS properties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200),
    type VARCHAR(50),
    location VARCHAR(150),
    size VARCHAR(50),
    price INT,
    owner VARCHAR(100),
    contact VARCHAR(50),
    status VARCHAR(50),
    sold_price INT DEFAULT 0
)
""")

# ================= PROPERTY INTERACTIONS =================
cur.execute("""
CREATE TABLE IF NOT EXISTS interactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    property_id INT,
    customer_name VARCHAR(100),
    contact VARCHAR(50),
    notes TEXT,
    date DATE,
    FOREIGN KEY (property_id) REFERENCES properties(id) ON DELETE CASCADE
)
""")

# ================= COLLABORATIONS =================
cur.execute("""
CREATE TABLE IF NOT EXISTS collaborations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    supplier VARCHAR(150),
    category VARCHAR(100),
    service VARCHAR(150),
    contact_person VARCHAR(100),
    contact_number VARCHAR(50),
    email VARCHAR(100),
    start_date DATE,
    due_date DATE,
    total_amount INT,
    paid_amount INT,
    pending_amount INT
)
""")

# ================= COLLABORATION INTERACTIONS =================
cur.execute("""
CREATE TABLE IF NOT EXISTS collaboration_interactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    collaboration_id INT,
    note TEXT,
    date DATE,
    FOREIGN KEY (collaboration_id) REFERENCES collaborations(id) ON DELETE CASCADE
)
""")

conn.commit()
conn.close()

print("✅ Database tanvidb and all tables created successfully")
