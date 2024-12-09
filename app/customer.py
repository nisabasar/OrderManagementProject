from app.database import get_database_connection

def insert_customer(name, budget):
    try:
        conn = get_database_connection()
        if conn is None:
            return "Veritabanı bağlantısı sağlanamadı."
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Customers (CustomerName, Budget)
            VALUES (%s, %s)
        """, (name, budget))
        conn.commit()
        print(f"Müşteri {name} başarıyla eklendi!")
        conn.close()
    except Exception as err:
        print(f"Müşteri eklenirken hata oluştu: {err}")
