import MySQLdb.cursors
from app.database import get_database_connection
from app.logs import insert_log
from app.customer import get_sorted_customers
import threading

# Tek bir siparişi işleyen ana fonksiyon
def process_order(order):
    try:
        print(f"Sipariş işleniyor: {order['OrderID']} - Müşteri: {order['CustomerID']}")
        
        # Örnek: Siparişi "Tamamlandı" olarak işaretle
        conn = get_database_connection()
        if conn is None:
            print("Veritabanı bağlantısı sağlanamadı.")
            return

        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Orders SET OrderStatus = 'Completed' WHERE OrderID = %s
        """, (order['OrderID'],))
        conn.commit()
        conn.close()

        # Log kaydet
        insert_log(order['CustomerID'], order['OrderID'], "Info", f"Sipariş başarıyla işleme alındı.")
    except Exception as err:
        print(f"Sipariş işlenirken hata oluştu: {err}")
        insert_log(order['CustomerID'], order['OrderID'], "Error", f"Sipariş sırasında hata oluştu: {err}")

# Sırayla sipariş işleme
def process_orders():
    try:
        conn = get_database_connection()
        if conn is None:
            print("Veritabanı bağlantısı sağlanamadı.")
            return

        cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        # Öncelikli müşterileri sırala
        sorted_customers = get_sorted_customers()

        for customer in sorted_customers:
            customer_id = customer['CustomerID']

            # Bekleyen siparişleri al
            cursor.execute("""
                SELECT * FROM Orders
                WHERE CustomerID = %s AND OrderStatus = 'Pending'
                ORDER BY OrderDate ASC
            """, (customer_id,))
            pending_orders = cursor.fetchall()

            for order in pending_orders:
                process_order(order)  # Tek siparişi işle

        conn.close()
        print("Tüm siparişler sırayla işlendi!")
    except Exception as err:
        print(f"Sipariş işleme hatası: {err}")
    finally:
        if 'conn' in locals() and conn is not None:
            conn.close()

# Eş zamanlı (paralel) sipariş işleme
def process_orders_concurrently():
    try:
        conn = get_database_connection()
        if conn is None:
            print("Veritabanı bağlantısı sağlanamadı.")
            return

        cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        # Bekleyen tüm siparişleri al
        cursor.execute("""
            SELECT * FROM Orders
            WHERE OrderStatus = 'Pending'
            ORDER BY OrderDate ASC
        """)
        pending_orders = cursor.fetchall()

        threads = []
        for order in pending_orders:
            # Tek siparişi işlemek için thread başlat
            t = threading.Thread(target=process_order, args=(order,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()  # Tüm thread'lerin bitmesini bekle

        conn.close()
        print("Tüm siparişler paralel olarak işlendi!")
    except Exception as err:
        print(f"Çoklu işlem hatası: {err}")
    finally:
        if 'conn' in locals() and conn is not None:
            conn.close()

# Yeni bir sipariş oluşturma
def create_order(customer_id, product_id, quantity):
    try:
        conn = get_database_connection()
        if conn is None:
            print("Veritabanı bağlantısı sağlanamadı.")
            return

        cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        # Müşteri ve ürün bilgilerini kontrol et
        cursor.execute("SELECT Budget, CustomerType FROM Customers WHERE CustomerID = %s", (customer_id,))
        customer = cursor.fetchone()

        cursor.execute("SELECT Stock, Price FROM Products WHERE ProductID = %s", (product_id,))
        product = cursor.fetchone()

        if not customer or not product:
            print("Geçersiz müşteri veya ürün.")
            return

        budget = customer['Budget']
        stock = product['Stock']
        price = product['Price']
        total_price = quantity * price

        if stock < quantity:
            print("Stok yetersiz.")
            cursor.execute("""
                INSERT INTO Orders (CustomerID, ProductID, Quantity, TotalPrice, OrderStatus)
                VALUES (%s, %s, %s, %s, 'Failed')
            """, (customer_id, product_id, quantity, total_price))
            conn.commit()
            insert_log(customer_id, None, "Error", f"Müşteri {customer_id} için sipariş başarısız: Stok yetersiz.")
            return

        if budget < total_price:
            print("Bütçe yetersiz.")
            cursor.execute("""
                INSERT INTO Orders (CustomerID, ProductID, Quantity, TotalPrice, OrderStatus)
                VALUES (%s, %s, %s, %s, 'Failed')
            """, (customer_id, product_id, quantity, total_price))
            conn.commit()
            insert_log(customer_id, None, "Error", f"Müşteri {customer_id} için sipariş başarısız: Bütçe yetersiz.")
            return

        # Sipariş başarılıysa güncellemeleri yap
        cursor.execute("UPDATE Products SET Stock = Stock - %s WHERE ProductID = %s", (quantity, product_id))
        cursor.execute("UPDATE Customers SET Budget = Budget - %s, TotalSpent = TotalSpent + %s WHERE CustomerID = %s", (total_price, total_price, customer_id))
        cursor.execute("""
            INSERT INTO Orders (CustomerID, ProductID, Quantity, TotalPrice, OrderStatus)
            VALUES (%s, %s, %s, %s, 'Completed')
        """, (customer_id, product_id, quantity, total_price))

        conn.commit()
        insert_log(customer_id, None, "Info", f"Sipariş başarıyla oluşturuldu: Müşteri {customer_id}")
        print("Sipariş başarıyla oluşturuldu!")
    except Exception as err:
        print(f"Sipariş oluşturulurken hata oluştu: {err}")
    finally:
        if 'conn' in locals() and conn is not None:
            conn.close()
