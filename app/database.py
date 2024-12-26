import MySQLdb
from MySQLdb.cursors import DictCursor

def get_database_connection():
    try:
        print("Veritabanına bağlanmayı deniyorum...")
        conn = MySQLdb.connect(
            host="localhost",  # MySQL sunucu adresi
            user="root",       # Kullanıcı adı
            passwd="12345",    # Şifre
            db="OrderManagement",  # Veritabanı adı
            cursorclass=DictCursor  # Sözlük biçiminde veri döndürmek için
        )
        print("Bağlantı başarılı!")
        return conn
    except MySQLdb.Error as err:
        print(f"MySQL bağlantı hatası: {err}")
        return None

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