from app.database import get_database_connection
from datetime import datetime

def create_order(customer_id, product_id, quantity):
    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        # Ürün ve müşteri bilgilerini kontrol et
        cursor.execute("SELECT Stock, Price FROM Products WHERE ProductID = %s", (product_id,))
        product = cursor.fetchone()

        cursor.execute("SELECT Budget, CustomerType FROM Customers WHERE CustomerID = %s", (customer_id,))
        customer = cursor.fetchone()

        if not product or not customer:
            print("Geçersiz müşteri veya ürün.")
            return

        stock, price = product
        budget, customer_type = customer
        total_price = quantity * price

        if quantity > stock:
            print("Stok yetersiz.")
            return

        if total_price > budget:
            print("Bakiye yetersiz.")
            return

        # Sipariş oluştur
        cursor.execute("""
            INSERT INTO Orders (CustomerID, ProductID, Quantity, TotalPrice, OrderStatus)
            VALUES (%s, %s, %s, %s, 'Pending')
        """, (customer_id, product_id, quantity, total_price))
        conn.commit()
        print("Sipariş başarıyla oluşturuldu ve admin onayı bekleniyor.")
        conn.close()
    except Exception as err:
        print(f"Sipariş oluşturulurken hata oluştu: {err}")
