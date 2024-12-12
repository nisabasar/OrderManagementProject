import MySQLdb.cursors
from app.database import get_database_connection
from app.logs import insert_log
from app.customer import get_sorted_customers
import threading

def process_order(order):
    # Sipariş işleme fonksiyonu
    print(f"Sipariş işleniyor: {order['OrderID']} - Müşteri: {order['CustomerID']}")
    # Burada sipariş işlemleri yapılabilir (örneğin stok güncelleme)

def process_orders_concurrently():
    try:
        conn = get_database_connection()
        if conn is None:
            print("Veritabanı bağlantısı sağlanamadı.")
            return

        cursor = conn.cursor()

        # Bekleyen tüm siparişleri al
        cursor.execute("""
            SELECT * FROM Orders
            WHERE OrderStatus = 'Pending'
            ORDER BY OrderDate ASC
        """)
        pending_orders = cursor.fetchall()

        threads = []
        for order in pending_orders:
            t = threading.Thread(target=process_order, args=(order,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        conn.close()
        print("Tüm siparişler işleme alındı!")
    except Exception as err:
        print(f"Çoklu işlem hatası: {err}")


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

        budget, customer_type = customer
        stock, price = product
        total_price = quantity * price

        if stock < quantity:
            print("Stok yetersiz.")
            cursor.execute("""
                INSERT INTO Orders (CustomerID, ProductID, Quantity, TotalPrice, OrderStatus)
                VALUES (%s, %s, %s, %s, 'Failed')
            """, (customer_id, product_id, quantity, total_price))
            conn.commit()
            insert_log(customer_id, None, "Error", f"Müşteri {customer_id} için sipariş başarısız: Stok yetersiz.")
            conn.close()
            return

        if budget < total_price:
            print("Bütçe yetersiz.")
            cursor.execute("""
                INSERT INTO Orders (CustomerID, ProductID, Quantity, TotalPrice, OrderStatus)
                VALUES (%s, %s, %s, %s, 'Failed')
            """, (customer_id, product_id, quantity, total_price))
            conn.commit()
            insert_log(customer_id, None, "Error", f"Müşteri {customer_id} için sipariş başarısız: Bütçe yetersiz.")
            conn.close()
            return

        # Sipariş başarılıysa stoğu ve bütçeyi güncelle
        cursor.execute("""
            UPDATE Products SET Stock = Stock - %s WHERE ProductID = %s
        """, (quantity, product_id))
        cursor.execute("""
            UPDATE Customers SET Budget = Budget - %s, TotalSpent = TotalSpent + %s WHERE CustomerID = %s
        """, (total_price, total_price, customer_id))
        cursor.execute("""
            INSERT INTO Orders (CustomerID, ProductID, Quantity, TotalPrice, OrderStatus)
            VALUES (%s, %s, %s, %s, 'Completed')
        """, (customer_id, product_id, quantity, total_price))

        conn.commit()
        insert_log(customer_id, cursor.lastrowid, "Info", f"Müşteri {customer_id} için sipariş başarıyla oluşturuldu.")
        print("Sipariş başarıyla oluşturuldu!")
        conn.close()
    except Exception as err:
        print(f"Sipariş oluşturulurken hata oluştu: {err}")


def process_orders():
    try:
        conn = get_database_connection()
        if conn is None:
            print("Veritabanı bağlantısı sağlanamadı.")
            return

        cursor = conn.cursor()

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
                print(f"Sipariş işleniyor: {order['OrderID']} - Müşteri: {customer['CustomerName']}")

                # Örnek: Siparişi "Tamamlandı" olarak işaretle
                cursor.execute("""
                    UPDATE Orders SET OrderStatus = 'Completed' WHERE OrderID = %s
                """, (order['OrderID'],))
                conn.commit()

        conn.close()
        print("Tüm siparişler işlendi!")
    except Exception as err:
        print(f"Sipariş işleme hatası: {err}")