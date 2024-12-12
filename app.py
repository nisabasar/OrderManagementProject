from flask import Flask, render_template
from app.customer import get_sorted_customers
from app.admin import check_critical_stock
from app.database import get_database_connection
from mysql.connector import connect, Error
from mysql.connector.cursor import MySQLCursorDict

app = Flask(__name__)

@app.route('/')
def home():
    # Müşteri öncelik sırasını al
    customers = get_sorted_customers()
    return render_template('home.html', customers=customers)

@app.route('/critical-stock')
def critical_stock():
    try:
        conn = get_database_connection()
        cursor = conn.cursor()  
        cursor.execute("SELECT ProductName, Stock FROM Products WHERE Stock < 10")
        critical_products = cursor.fetchall()
        conn.close()
        return render_template('critical_stock.html', products=critical_products)
    except Error as e:
        print(f"Hata oluştu: {e}")
        return "Bir hata oluştu.", 500
    
if __name__ == '__main__':
    app.run(debug=True)
