import MySQLdb

def get_database_connection():
    try:
        print("Veritabanına bağlanmayı deniyorum...")
        conn = MySQLdb.connect(
            host="localhost",  # MySQL sunucu adresi
            user="root",       # Kullanıcı adı
            passwd="12345",    # Şifre
            db="OrderManagement"  # Veritabanı adı
        )
        print("Bağlantı başarılı!")
        return conn
    except MySQLdb.Error as err:
        print(f"MySQL bağlantı hatası: {err}")
        return None
