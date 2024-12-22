from flask import Flask, render_template, request, redirect, url_for, session
from app.database import get_database_connection
import MySQLdb

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Admin Panel: Yeni Admin Eklenmesi
@app.route('/add-admin', methods=['GET', 'POST'])
def add_admin():
    if 'role' not in session or session['role'] != 'Admin':
        return "Yetkiniz yok!", 403

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = get_database_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Users (Username, Password, Role) VALUES (%s, %s, 'Admin')", (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('admin_dashboard'))
        except Exception as e:
            return f"Hata: {e}", 500

    return render_template('add_admin.html')

# Kullanıcı Girişi
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = get_database_connection()
            cursor = conn.cursor()
            
            # Kullanıcıyı doğrula
            cursor.execute("SELECT * FROM Users WHERE Username = %s AND Password = %s", (username, password))
            user = cursor.fetchone()
            conn.close()

            if user:
                session['user_id'] = user['UserID']
                session['role'] = user['Role']
                if user['Role'] == 'Admin':
                    return redirect(url_for('admin_panel'))
                elif user['Role'] == 'Customer':
                    return redirect(url_for('customer_panel'))
                else:
                    return "Bilinmeyen kullanıcı rolü!", 403
            else:
                return "Kullanıcı adı veya şifre hatalı!", 401
        except Exception as e:
            return f"Hata: {e}", 500

    return render_template('login.html')

# Kayıt Olma
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        customer_name = request.form['customer_name']
        budget = float(request.form['budget'])
        customer_type = request.form['customer_type']

        try:
            conn = get_database_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO Users (Username, Password, Role) VALUES (%s, %s, 'Customer')", (username, password))
            user_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO Customers (CustomerName, Budget, CustomerType, UserID)
                VALUES (%s, %s, %s, %s)
            """, (customer_name, budget, customer_type, user_id))

            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except Exception as e:
            return f"Hata: {e}", 500

    return render_template('register.html')

# Admin Dashboard
@app.route('/admin-dashboard')
def admin_dashboard():
    if 'role' not in session or session['role'] != 'Admin':
        return "Yetkiniz yok!", 403

    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Orders WHERE OrderStatus = 'Pending'")
        orders = cursor.fetchall()
        conn.close()

        return render_template('admin_dashboard.html', orders=orders)
    except Exception as e:
        return f"Hata: {e}", 500

# Müşteri Paneli
@app.route('/customer-panel', methods=['GET', 'POST'])
def customer_panel():
    if 'role' not in session or session['role'] != 'Customer':
        return redirect(url_for('login'))

    customer_id = session['user_id']

    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        # Müşteri bilgilerini çek
        cursor.execute("SELECT * FROM Customers WHERE UserID = %s", (customer_id,))
        customer_info = cursor.fetchone()

        # Ürün bilgilerini çek
        cursor.execute("SELECT * FROM Products")
        products = cursor.fetchall()

        # Sepeti çek
        cart = session.get('cart', [])

        conn.close()

        return render_template('customer_panel.html', customer_info=customer_info, products=products, cart=cart)
    except Exception as e:
        return f"Hata: {e}", 500

# Sepete Ekleme
@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])

    conn = get_database_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ProductName, Stock, Price FROM Products WHERE ProductID = %s", (product_id,))
    product = cursor.fetchone()

    if not product or product[1] < quantity:
        return "Stok yetersiz!", 400

    cart = session.get('cart', [])
    cart.append({
        'ProductID': product_id,
        'ProductName': product[0],
        'Quantity': quantity,
        'TotalPrice': product[2] * quantity
    })
    session['cart'] = cart

    conn.close()
    return redirect(url_for('customer_panel'))

# Siparişi Tamamlama
@app.route('/submit-order', methods=['POST'])
def submit_order():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    customer_id = session['user_id']
    cart = session.get('cart', [])

    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        for item in cart:
            cursor.execute("INSERT INTO Orders (CustomerID, ProductID, Quantity, TotalPrice, OrderStatus) VALUES (%s, %s, %s, %s, 'Pending')",
                           (customer_id, item['ProductID'], item['Quantity'], item['TotalPrice']))

            cursor.execute("UPDATE Products SET Stock = Stock - %s WHERE ProductID = %s",
                           (item['Quantity'], item['ProductID']))

        conn.commit()
        session['cart'] = []  # Sepeti temizle
        conn.close()

        return redirect(url_for('customer_panel'))
    except Exception as e:
        return f"Hata: {e}", 500
    
@app.route('/admin-panel', methods=['GET', 'POST'])
def admin_panel():
    if 'role' not in session or session['role'] != 'Admin':
        return "Yetkiniz yok!", 403

    try:
        conn = get_database_connection()
        cursor = conn.cursor()

         # Ürünleri ve kritik stokları çek
        cursor.execute("SELECT * FROM Products")
        products = cursor.fetchall()
        cursor.execute("SELECT * FROM Products WHERE Stock < 10")
        critical_products = cursor.fetchall()
    
        cursor.execute("""
        SELECT CustomerID, CustomerName, Budget, CustomerType, TotalSpent, PriorityScore
        FROM Customers
        ORDER BY PriorityScore DESC
        """)

        # Siparişleri al
        cursor.execute("""
            SELECT o.OrderID, c.CustomerName, p.ProductName, o.Quantity, o.TotalPrice, o.OrderStatus
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            JOIN Products p ON o.ProductID = p.ProductID
        """)
        orders = cursor.fetchall()

        # Müşterileri al
        cursor.execute("""
            SELECT CustomerID, CustomerName, Budget, TotalSpent, CustomerType, PriorityScore
            FROM Customers
        """)
        customers = cursor.fetchall()

        # Logları al
        cursor.execute("""
            SELECT LogID, CustomerID, LogType, LogDetails, LogDate
            FROM Logs
        """)
        logs = cursor.fetchall()

        conn.close()

        return render_template(
            'admin_panel.html',
            products=products,
            orders=orders,
            customers=customers,
            logs=logs
        )
    except Exception as e:
        return f"Hata: {e}", 500


@app.route('/add-product', methods=['POST'])
def add_product():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    product_name = request.form['product_name']
    stock = int(request.form['stock'])
    price = float(request.form['price'])

    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Products (ProductName, Stock, Price)
            VALUES (%s, %s, %s)
        """, (product_name, stock, price))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_panel'))
    except Exception as e:
        return f"Hata: {e}", 500

@app.route('/update-product-stock', methods=['POST'])
def update_product_stock():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    product_id = int(request.form['product_id'])
    new_stock = int(request.form['new_stock'])

    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Products SET Stock = %s WHERE ProductID = %s
        """, (new_stock, product_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_panel'))
    except Exception as e:
        return f"Hata: {e}", 500
    
@app.route('/delete-product', methods=['POST'])
def delete_product():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    product_id = int(request.form['product_id'])

    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Products WHERE ProductID = %s", (product_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_panel'))
    except Exception as e:
        return f"Hata: {e}", 500
    
@app.route('/approve-order', methods=['POST'])
def approve_order():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    order_id = int(request.form['order_id'])

    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Orders SET OrderStatus = 'Approved' WHERE OrderID = %s
        """, (order_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_panel'))
    except Exception as e:
        return f"Hata: {e}", 500

@app.route('/reject-order', methods=['POST'])
def reject_order():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    order_id = int(request.form['order_id'])

    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Orders SET OrderStatus = 'Rejected' WHERE OrderID = %s
        """, (order_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_panel'))
    except Exception as e:
        return f"Hata: {e}", 500
    
@app.route('/filter-logs', methods=['POST'])
def filter_logs():
    log_type = request.form['log_type']
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        if log_type == "All":
            cursor.execute("SELECT * FROM Logs")
        else:
            cursor.execute("SELECT * FROM Logs WHERE LogType = %s", (log_type,))
        logs = cursor.fetchall()
        conn.close()
        return render_template('admin_panel.html', logs=logs)
    except Exception as e:
        return f"Error: {e}", 500

    
@app.route('/change-customer-type', methods=['POST'])
def change_customer_type():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    customer_id = int(request.form['customer_id'])
    new_type = request.form['customer_type']

    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE Customers SET CustomerType = %s WHERE CustomerID = %s
        """, (new_type, customer_id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_panel'))
    except Exception as e:
        return f"Hata: {e}", 500

@app.route('/admin-add-product', methods=['POST'])
def admin_add_product():
    if 'role' not in session or session['role'] != 'Admin':
        return redirect(url_for('login'))

    product_name = request.form['product_name']
    stock = int(request.form['stock'])
    price = float(request.form['price'])

    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Products (ProductName, Stock, Price)
            VALUES (%s, %s, %s)
        """, (product_name, stock, price))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_panel'))
    except Exception as e:
        return f"Hata: {e}", 500

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
