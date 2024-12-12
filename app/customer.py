import random
import MySQLdb
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
    except MySQLdb.Error as err:
        print(f"Müşteri eklenirken hata oluştu: {err}")


def insert_random_customers():
    try:
        conn = get_database_connection()
        if conn is None:
            print("Veritabanı bağlantısı sağlanamadı.")
            return

        cursor = conn.cursor()

        # Rastgele müşteri oluşturma
        customer_types = ['Standard', 'Premium']
        premium_count = 0  # En az 2 Premium müşteri eklemek için sayaç

        for _ in range(random.randint(5, 10)):  # 5-10 müşteri arasında oluştur
            name = f"Customer{random.randint(1, 1000)}"
            budget = round(random.uniform(500, 3000), 2)  # 500-3000 TL arasında bütçe
            if premium_count < 2:  # Başlangıçta en az 2 Premium müşteri olsun
                customer_type = 'Premium'
                premium_count += 1
            else:
                customer_type = random.choice(customer_types)

            # Veritabanına müşteri ekleme
            cursor.execute("""
                INSERT INTO Customers (CustomerName, Budget, CustomerType)
                VALUES (%s, %s, %s)
            """, (name, budget, customer_type))

        conn.commit()
        print("Rastgele müşteriler başarıyla eklendi!")
        conn.close()
    except Exception as err:
        print(f"Müşteri eklenirken hata oluştu: {err}")