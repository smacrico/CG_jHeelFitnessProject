# database in pgAdmin

import psycopg2

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host="localhost",
    database="garminDB_v2",
    user="postgres",
    password="Penivalia2627"
)

# Create a cursor
cursor = conn.cursor()

###################

# Execute SQL queries using the cursor
###################
###################

cursor.execute("CREATE TABLE your_table_name (...)")
# cursor.execute("CREATE TABLE your_table_name (...)")

