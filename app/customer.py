import random
import MySQLdb
import MySQLdb.cursors
import time
from app.database import get_database_connection

def insert_customer(name, budget):
    try:
        conn = get_database_connection()
        if conn is None:
            return "Veritabanı bağlantısı sağlanamadı."

        cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
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

        cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)

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

def update_all_customers_priority():
    try:
        conn = get_database_connection()
        if conn is None:
            print("Veritabanı bağlantısı sağlanamadı.")
            return

        cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT CustomerID FROM Customers")
        customers = cursor.fetchall()

        # Her müşteri için öncelik skorunu hesapla
        for customer in customers:
            customer_id = customer[0]
            order_time = time.time() - 10  # Örnek olarak 10 saniye önce sipariş verilmiş gibi kabul ediyoruz
            calculate_priority_score(customer_id, order_time)

        conn.close()
    except Exception as err:
        print(f"Tüm müşteriler için öncelik skoru güncellenirken hata oluştu: {err}")


def calculate_priority_score(customer_id, order_time):
    try:
        conn = get_database_connection()
        if conn is None:
            print("Veritabanı bağlantısı sağlanamadı.")
            return

        cursor = conn.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        # Müşteri bilgilerini al
        cursor.execute("SELECT CustomerType FROM Customers WHERE CustomerID = %s", (customer_id,))
        customer = cursor.fetchone()

        if not customer:
            print("Müşteri bulunamadı.")
            return

        customer_type = customer[0]

        # Temel öncelik skoru
        base_score = 15 if customer_type == "Premium" else 10

        # Bekleme süresini hesapla
        current_time = time.time()
        waiting_time = current_time - order_time
        waiting_weight = 0.5
        waiting_score = waiting_time * waiting_weight

        # Toplam öncelik skorunu hesapla
        priority_score = base_score + waiting_score

        # Veritabanında güncelle
        cursor.execute("""
            UPDATE Customers SET PriorityScore = %s WHERE CustomerID = %s
        """, (priority_score, customer_id))
        conn.commit()
        print(f"Müşteri {customer_id} için öncelik skoru güncellendi: {priority_score:.2f}")
        conn.close()
    except Exception as err:
        print(f"Öncelik skoru hesaplanırken hata oluştu: {err}")


def get_sorted_customers():
    try:
        conn = get_database_connection()
        if conn is None:
            print("Veritabanı bağlantısı sağlanamadı.")
            return []

        cursor = conn.cursor()
        cursor.execute("""
            SELECT CustomerID, CustomerName, CustomerType, PriorityScore
            FROM Customers
            ORDER BY PriorityScore DESC
        """)
        customers = cursor.fetchall()
        conn.close()
        return customers
    except Exception as err:
        print(f"Müşteri sıralama hatası: {err}")
        return []