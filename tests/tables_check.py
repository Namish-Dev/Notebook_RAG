import sqlite3

# Connecting to the database
conn = sqlite3.connect("notes.db")
cursor = conn.cursor()

# Getting all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")

tables = cursor.fetchall()

print("Tables in the database:")
for table in tables:
    print(table[0])

conn.close()