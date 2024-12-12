from app.database import get_database_connection
from app.logs import insert_log

def create_order(customer_id, product_id, quantity):
    try:
        conn = get_database_connection()
        if conn is None:
            print("Veritabanı bağlantısı sağlanamadı.")
            return

        cursor = conn.cursor()

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
