from app.database import get_database_connection

def add_product(name, stock, price):
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Products (ProductName, Stock, Price)
            VALUES (%s, %s, %s)
        """, (name, stock, price))
        conn.commit()
        print(f"Ürün {name} başarıyla eklendi!")
        conn.close()
    except Exception as err:
        print(f"Ürün eklenirken hata oluştu: {err}")

def update_stock(product_id, new_stock):
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Products SET Stock = %s WHERE ProductID = %s
        """, (new_stock, product_id))
        conn.commit()
        print(f"Ürün stoğu güncellendi!")
        conn.close()
    except Exception as err:
        print(f"Stok güncellenirken hata oluştu: {err}")

def delete_product(product_id):
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Products WHERE ProductID = %s", (product_id,))
        conn.commit()
        print(f"Ürün silindi!")
        conn.close()
    except Exception as err:
        print(f"Ürün silinirken hata oluştu: {err}")
