from flask import Flask, render_template, request
from app.customer import get_sorted_customers
from app.admin import check_critical_stock
from app.database import get_database_connection
from mysql.connector import connect, Error
from mysql.connector.cursor import MySQLCursorDict
import json
from flask import jsonify

app = Flask(__name__)

@app.route('/')
def home():
    # Müşteri öncelik sırasını al
    customers = get_sorted_customers()
    return render_template('home.html', customers=customers)

@app.route('/create-order', methods=['GET', 'POST'])
def create_order():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])

        conn = get_database_connection()
        cursor = conn.cursor()

        # Ürün ve müşteri bilgilerini kontrol et
        cursor.execute("SELECT Stock, Price FROM Products WHERE ProductID = %s", (product_id,))
        product = cursor.fetchone()
        cursor.execute("SELECT Budget FROM Customers WHERE CustomerID = %s", (customer_id,))
        customer = cursor.fetchone()

        if product['Stock'] < quantity:
            return "Stok yetersiz!"
        if customer['Budget'] < (quantity * product['Price']):
            return "Bütçe yetersiz!"

        # Sipariş ekle
        total_price = quantity * product['Price']
        cursor.execute("""
            INSERT INTO Orders (CustomerID, ProductID, Quantity, TotalPrice, OrderStatus)
            VALUES (%s, %s, %s, %s, 'Completed')
        """, (customer_id, product_id, quantity, total_price))

        # Stok ve bütçeyi güncelle
        cursor.execute("UPDATE Products SET Stock = Stock - %s WHERE ProductID = %s", (quantity, product_id))
        cursor.execute("UPDATE Customers SET Budget = Budget - %s WHERE CustomerID = %s", (total_price, customer_id))
        conn.commit()
        conn.close()

        return "Sipariş başarıyla oluşturuldu!"

    # GET request için müşteri ve ürün listesi
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT CustomerID, CustomerName FROM Customers")
    customers = cursor.fetchall()
    cursor.execute("SELECT ProductID, ProductName FROM Products")
    products = cursor.fetchall()
    conn.close()
    return render_template('create_order.html', customers=customers, products=products)

@app.route('/update-stock', methods=['GET', 'POST'])
def update_stock():
    if request.method == 'POST':
        product_id = request.form['product_id']
        new_stock = request.form['new_stock']

        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Products SET Stock = %s WHERE ProductID = %s", (new_stock, product_id))
        conn.commit()
        conn.close()

        return "Stok başarıyla güncellendi!"
    
    # GET request için tüm ürünleri listeleyin
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ProductID, ProductName, Stock FROM Products")
    products = cursor.fetchall()
    conn.close()
    return render_template('update_stock.html', products=products)


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
    
@app.route('/stock-data')
def stock_data():
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ProductName, Stock FROM Products")
        products = cursor.fetchall()
        conn.close()
        
        # Veriyi JSON olarak döndür
        return jsonify(products)
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return jsonify({'error': 'Veri alınırken bir hata oluştu.'}), 500
    
@app.route('/stock-chart')
def stock_chart():
    return render_template('stock_chart.html')

if __name__ == '__main__':
    app.run(debug=True)
