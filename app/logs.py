from app.database import get_database_connection


def insert_log(customer_id=None, order_id=None, log_type="Info", details="", customer_type=None, product_id=None, quantity=None, result=None):
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Logs (CustomerID, OrderID, LogType, LogDetails, ProductID, Quantity, Result, LogDate)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """, (customer_id, order_id, log_type, details, product_id, quantity, result))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Log kaydedilirken hata oluştu: {e}")
