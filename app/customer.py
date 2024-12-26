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


import random
import MySQLdb
from app.database import get_database_connection

def insert_random_customers():
    try:
        conn = get_database_connection()
        if conn is None:
            print("Veritabanı bağlantısı sağlanamadı.")
            return

        cursor = conn.cursor()

        customer_types = ['Standard', 'Premium']
        premium_count = 0  # En az 2 Premium müşteri için sayaç

        for _ in range(random.randint(5, 10)):  # 5-10 müşteri oluştur
            name = f"Customer{random.randint(1, 1000)}"
            budget = round(random.uniform(500, 3000), 2)  # 500-3000 TL arasında bütçe
            username = f"user{random.randint(1000, 9999)}"
            password = f"pass{random.randint(1000, 9999)}"
            if premium_count < 2:
                customer_type = 'Premium'
                premium_count += 1
            else:
                customer_type = random.choice(customer_types)

            # Kullanıcı ekleme
            cursor.execute("INSERT INTO Users (Username, Password) VALUES (%s, %s)", (username, password))
            user_id = cursor.lastrowid

            # Müşteri ekleme
            cursor.execute("""
                INSERT INTO Customers (CustomerName, Budget, CustomerType, UserID)
                VALUES (%s, %s, %s, %s)
            """, (name, budget, customer_type, user_id))

        conn.commit()
        print("Rastgele müşteriler ve kullanıcılar başarıyla eklendi!")
        conn.close()
    except MySQLdb.Error as err:
        print(f"Hata: {err}")


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

def remove_expired_cart_items():
    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        # 20 saniyeden eski ürünleri sepetten kaldır
        cursor.execute("""
            DELETE FROM Cart 
            WHERE TIMESTAMPDIFF(SECOND, AddedTime, NOW()) > 20
        """)

        conn.commit()
    finally:
        cursor.close()
        conn.close()


import time

def calculate_priority_score(customer, current_time):
    """
    Müşteri öncelik skorunu hesaplar.
    """
    # Temel öncelik skoru
    base_priority = 15 if customer['CustomerType'] == 'Premium' else 10

    # Bekleme süresi
    if customer['LastOrderDate']:
        waiting_time_seconds = (current_time - customer['LastOrderDate']).total_seconds()
    else:
        waiting_time_seconds = 0

    # Bekleme süresi ağırlığı
    waiting_time_weight = 0.5

    # Dinamik öncelik skoru
    return base_priority + int(waiting_time_seconds * waiting_time_weight)




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