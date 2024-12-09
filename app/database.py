import mysql.connector

def get_database_connection():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345",
            database="ordermanagement"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"MySQL bağlantı hatası: {err}")
        return None
