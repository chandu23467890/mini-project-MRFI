#!/usr/bin/env python3
import sqlite3
import os

db_path = 'instance/metabolic_stability.db'

try:
    # Check if file exists
    if not os.path.exists(db_path):
        print("Database file does not exist")
        exit(1)
    
    # Try to connect
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables found:", [row[0] for row in tables])
    
    # Check integrity
    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchone()
    print("Integrity check:", integrity[0])
    
    # Count records in each table
    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        print(f"  {table_name}: {count} records")
    
    conn.close()
    print("\nDatabase is accessible!")
    
except sqlite3.DatabaseError as e:
    print(f"Database Error: {e}")
    print("Database appears to be corrupted!")
except Exception as e:
    print(f"Error: {e}")
