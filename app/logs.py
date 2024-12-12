from app.database import get_database_connection

def insert_log(customer_id, order_id, log_type, details):
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Logs (CustomerID, OrderID, LogType, LogDetails)
            VALUES (%s, %s, %s, %s)
        """, (customer_id, order_id, log_type, details))
        conn.commit()
        print(f"[LOG] {log_type}: {details}")  # Terminalde logları göster
        conn.close()
    except Exception as e:
        print(f"Log eklenirken hata oluştu: {e}")
