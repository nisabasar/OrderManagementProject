from app.database import get_database_connection

def insert_log(customer_id=None, order_id=None, log_type="Info", details=""):
    try:
        conn = get_database_connection()
        if conn is None:
            print("Veritabanı bağlantısı sağlanamadı.")
            return

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
