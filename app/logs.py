from app.database import get_database_connection

def insert_log(customer_id, order_id, log_type, details):
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
        print(f"Log kaydedildi: {details}")
        conn.close()
    except Exception as err:
        print(f"Log eklenirken hata oluştu: {err}")
