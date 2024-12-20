from flask import Flask, render_template, request, jsonify
from app.customer import get_sorted_customers
from app.admin import check_critical_stock
from app.database import get_database_connection
from app.logs import insert_log
from mysql.connector import Error

app = Flask(__name__)

@app.route('/')
def home():
    customers = get_sorted_customers()
    return render_template('home.html', customers=customers)

@app.route('/create-order', methods=['GET', 'POST'])
def create_order():
    if request.method == 'POST':
        customer_id = request.form['customer_id']
        product_id = request.form['product_id']
        quantity = int(request.form['quantity'])

        try:
            conn = get_database_connection()
            cursor = conn.cursor()

            # Ürün ve müşteri bilgilerini kontrol et
            cursor.execute("SELECT Stock, Price FROM Products WHERE ProductID = %s", (product_id,))
            product = cursor.fetchone()
            cursor.execute("SELECT Budget, CustomerType FROM Customers WHERE CustomerID = %s", (customer_id,))
            customer = cursor.fetchone()

            if not product or not customer:
                insert_log(customer_id, None, "Error", "Ürün veya müşteri bulunamadı.", customer_type=None, product_id=product_id, quantity=quantity, result="Başarısız")
                return "Ürün veya müşteri bulunamadı!"

            if product['Stock'] < quantity:
                insert_log(customer_id, None, "Error", f"Stok yetersiz: {product_id} ID'li ürün için {quantity} talep edildi, mevcut stok: {product['Stock']}", customer_type=customer['CustomerType'], product_id=product_id, quantity=quantity, result="Başarısız")
                return "Stok yetersiz!"

            if customer['Budget'] < (quantity * product['Price']):
                insert_log(customer_id, None, "Error", f"Bütçe yetersiz: {customer_id} ID'li müşteri için toplam fiyat {quantity * product['Price']}, mevcut bütçe: {customer['Budget']}", customer_type=customer['CustomerType'], product_id=product_id, quantity=quantity, result="Başarısız")
                return "Bütçe yetersiz!"

            # Sipariş ekle
            total_price = quantity * product['Price']
            cursor.execute("""
                INSERT INTO Orders (CustomerID, ProductID, Quantity, TotalPrice, OrderStatus)
                VALUES (%s, %s, %s, %s, 'Completed')
            """, (customer_id, product_id, quantity, total_price))
            order_id = cursor.lastrowid

            # Stok ve bütçeyi güncelle
            cursor.execute("UPDATE Products SET Stock = Stock - %s WHERE ProductID = %s", (quantity, product_id))
            cursor.execute("UPDATE Customers SET Budget = Budget - %s WHERE CustomerID = %s", (total_price, customer_id))

            conn.commit()
            insert_log(customer_id, order_id, "Info", f"Müşteri {customer_id} {quantity} adet {product_id} ID'li ürünü satın aldı.", customer_type=customer['CustomerType'], product_id=product_id, quantity=quantity, result="Başarılı")
            return "Sipariş başarıyla oluşturuldu!"
        except Exception as e:
            insert_log(customer_id, None, "Error", f"Sipariş oluşturulurken hata: {e}", customer_type=None, product_id=product_id, quantity=quantity, result="Başarısız")
            return f"Bir hata oluştu: {e}", 500
        finally:
            conn.close()

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
        new_stock = int(request.form['new_stock'])

        try:
            conn = get_database_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE Products SET Stock = %s WHERE ProductID = %s", (new_stock, product_id))
            conn.commit()
            insert_log(None, None, "Info", f"Admin, {product_id} ID'li ürünün stok seviyesini {new_stock} olarak güncelledi.", product_id=product_id, quantity=new_stock, result="Başarılı")
            return "Stok başarıyla güncellendi!"
        except Exception as e:
            insert_log(None, None, "Error", f"Stok güncellenirken hata: {e}", product_id=product_id, result="Başarısız")
            return f"Bir hata oluştu: {e}", 500
        finally:
            conn.close()

    # GET request için ürünleri listele
    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ProductID, ProductName, Stock FROM Products")
    products = cursor.fetchall()
    conn.close()
    return render_template('update_stock.html', products=products)

@app.route('/logs')
def view_logs():
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                Logs.LogID,
                Logs.CustomerID,
                Logs.OrderID,
                Customers.CustomerType,
                Logs.ProductID,
                Logs.Quantity,
                Logs.LogType,
                Logs.Result,
                Logs.LogDetails,
                Logs.LogDate
            FROM Logs
            LEFT JOIN Customers ON Logs.CustomerID = Customers.CustomerID
            ORDER BY Logs.LogDate DESC
        """)
        logs = cursor.fetchall()
        conn.close()
        return render_template('logs.html', logs=logs)
    except Exception as e:
        print(f"Loglar getirilirken hata oluştu: {e}")
        return "Loglar görüntülenirken bir hata oluştu.", 500

@app.route('/critical-stock')
def critical_stock():
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ProductName, Stock FROM Products WHERE Stock < 10")
        critical_products = cursor.fetchall()
        conn.close()
        insert_log(None, None, "Info", "Kritik stok kontrolü yapıldı.")
        return render_template('critical_stock.html', products=critical_products)
    except Error as e:
        insert_log(None, None, "Error", f"Kritik stok sorgusunda hata: {e}")
        return "Bir hata oluştu.", 500

@app.route('/stock-data')
def stock_data():
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT ProductName, Stock FROM Products")
        products = cursor.fetchall()
        conn.close()
        insert_log(None, None, "Info", "Grafik için stok verileri alındı.")
        return jsonify(products)
    except Exception as e:
        insert_log(None, None, "Error", f"Stok verisi alınırken hata: {e}")
        return jsonify({'error': 'Veri alınırken bir hata oluştu.'}), 500

@app.route('/stock-chart')
def stock_chart():
    return render_template('stock_chart.html')

if __name__ == '__main__':
    app.run(debug=True)