# src/database.py

import psycopg2

def connect_to_sql():
    """Establishes a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host="localhost",
            user="postgres",
            port="5432",
            database="youtube",
            password="mani94"
        )
        return conn
    except psycopg2.Error as e:
        print("Error connecting to PostgreSQL database:", e)
        return None

def execute_query(query, columns):
    """Executes the given SQL query and returns the result."""
    conn = connect_to_sql()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
            conn.close()
            return data
        except psycopg2.Error as e:
            print("Error executing SQL query:", e)
            return None
    else:
        return None
