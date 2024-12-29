import traceback
from flask import Flask, jsonify, render_template, request, redirect, url_for, session
from app import customer
from app.database import get_database_connection
from datetime import datetime
import MySQLdb

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Loglama Fonksiyonu
def log_action(customer_id, log_type, details):
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Logs (CustomerID, LogType, LogDetails, LogDate)
            VALUES (%s, %s, %s, NOW())
        """, (customer_id, log_type, details))
        conn.commit()
    except Exception as e:
        print(f"Loglama sırasında hata oluştu: {e}")
    finally:
        cursor.close()
        conn.close()


@app.route('/update-stock', methods=['POST'])
def update_stock():
    try:
        data = request.get_json()
        product_id = int(data.get('product_id'))
        new_stock = int(data.get('new_stock'))

        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE Products SET Stock = %s WHERE ProductID = %s", (new_stock, product_id))
        conn.commit()

        # Güncellenmiş ürünleri ve kritik ürünleri al
        cursor.execute("SELECT * FROM Products")
        products = cursor.fetchall()
        cursor.execute("SELECT * FROM Products WHERE Stock < 10")
        critical_products = cursor.fetchall()

        return jsonify({
            "success": True,
            "message": "Stok başarıyla güncellendi.",
            "products": products,
            "critical_products": critical_products
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Hata: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()



@app.route('/delete-product', methods=['POST'])
def delete_product():
    try:
        data = request.get_json()
        product_id = int(data.get('product_id'))

        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Products WHERE ProductID = %s", (product_id,))
        conn.commit()

        # Güncellenmiş ürünleri ve kritik ürünleri al
        cursor.execute("SELECT * FROM Products")
        products = cursor.fetchall()
        cursor.execute("SELECT * FROM Products WHERE Stock < 10")
        critical_products = cursor.fetchall()

        return jsonify({
            "success": True,
            "message": "Ürün başarıyla silindi.",
            "products": products,
            "critical_products": critical_products
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Hata: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/add-product', methods=['POST'])
def add_product():
    try:
        data = request.get_json()
        product_name = data.get('product_name')
        stock = int(data.get('stock'))
        price = float(data.get('price'))

        if not (product_name and stock and price):
            return jsonify({"success": False, "message": "Tüm alanlar doldurulmalıdır."}), 400

        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Products (ProductName, Stock, Price) VALUES (%s, %s, %s)", (product_name, stock, price))
        conn.commit()

        # Güncellenmiş ürünleri ve kritik ürünleri al
        cursor.execute("SELECT * FROM Products")
        products = cursor.fetchall()
        cursor.execute("SELECT * FROM Products WHERE Stock < 10")
        critical_products = cursor.fetchall()

        return jsonify({
            "success": True,
            "message": "Ürün başarıyla eklendi.",
            "products": products,
            "critical_products": critical_products
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Hata: {str(e)}"}), 500
    finally:
        cursor.close()
        conn.close()




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
            log_action(None, "Info", f"Yeni admin eklendi: {username}")
            return redirect(url_for('admin_panel'))
        except Exception as e:
            return f"Hata: {e}", 500

    return render_template('add_admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            conn = get_database_connection()
            cursor = conn.cursor()

            # Kullanıcı bilgilerini doğrula
            cursor.execute("SELECT * FROM Users WHERE Username = %s AND Password = %s", (username, password))
            user = cursor.fetchone()

            if user:
                # Kullanıcı oturum bilgilerini session'a kaydet
                session['user_id'] = user['UserID']
                session['role'] = user['Role']

                if user['Role'] == 'Customer':
                    cursor.execute("SELECT CustomerID FROM Customers WHERE UserID = %s", (user['UserID'],))
                    customer = cursor.fetchone()

                    # Eğer müşteri kaydı yoksa hata döndür
                    if not customer or 'CustomerID' not in customer:
                        log_action(user['UserID'], "Error", f"Müşteri bilgileri bulunamadı: {username}")
                        return render_template('login.html', error="Müşteri bilgileri eksik! Lütfen yöneticiye başvurun.")

                    # Müşteri ID'sini session'a kaydet
                    session['customer_id'] = customer['CustomerID']

                log_action(user['UserID'], "Info", f"Kullanıcı giriş yaptı: {username}")

                # Role'e göre yönlendirme yap
                if user['Role'] == 'Admin':
                    return redirect(url_for('admin_panel'))
                elif user['Role'] == 'Customer':
                    return redirect(url_for('customer_panel'))
                else:
                    log_action(user['UserID'], "Warning", f"Bilinmeyen kullanıcı rolü: {username}")
                    return render_template('login.html', error="Bilinmeyen kullanıcı rolü!")

            else:
                log_action(None, "Warning", f"Geçersiz giriş denemesi: {username}")
                return render_template('login.html', error="Kullanıcı adı veya şifre hatalı!")

        except Exception as e:
            error_message = f"Giriş işleminde hata: {e}"
            print(traceback.format_exc())
            log_action(None, "Error", error_message)
            return render_template('login.html', error=error_message)

        finally:
            cursor.close()
            conn.close()

    return render_template('login.html')


@app.route('/check-session')
def check_session():
    return jsonify(session)

# Kısıtlamalar ile her endpointin loglanması
@app.before_request
def restrict_and_log():
    if 'role' in session:
        log_action(session.get('user_id'), "Info", f"Endpoint ziyaret edildi: {request.path}")
    else:
        log_action(None, "Warning", f"Yetkisiz erişim denemesi: {request.path}")

# Kayıt Olma
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        customer_name = request.form['customer_name']
        budget = request.form['budget']
        customer_type = request.form['customer_type']

        try:
            conn = get_database_connection()
            cursor = conn.cursor()

            # Kullanıcı ve müşteri ekleme
            cursor.execute("INSERT INTO Users (Username, Password, Role) VALUES (%s, %s, 'Customer')", (username, password))
            user_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO Customers (CustomerName, Budget, CustomerType, UserID)
                VALUES (%s, %s, %s, %s)
            """, (customer_name, budget, customer_type, user_id))

            conn.commit()
            log_action(user_id, "Info", f"Yeni müşteri kaydedildi: {customer_name}")
            return redirect(url_for('login'))

        except Exception as e:
            error_message = f"Kayıt hatası: {e}"
            print(traceback.format_exc())
            log_action(None, "Error", error_message)
            return render_template('register.html', error=error_message)

        finally:
            cursor.close()
            conn.close()

    return render_template('register.html')

@app.route('/customer-orders', methods=['GET'])
def customer_orders():
    if 'role' not in session or session['role'] != 'Customer':
        return jsonify({"success": False, "error": "Yetkisiz erişim!"})

    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        # Kullanıcının siparişlerini al
        cursor.execute("""
            SELECT o.OrderID, p.ProductName, o.Quantity, o.OrderStatus
            FROM Orders o
            JOIN Products p ON o.ProductID = p.ProductID
            WHERE o.CustomerID = %s
        """, (session['customer_id'],))
        orders = cursor.fetchall()

        return jsonify({"success": True, "orders": orders})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
@app.route('/customer-info', methods=['GET'])
def customer_info():
    if 'role' not in session or session['role'] != 'Customer':
        return jsonify({"success": False, "error": "Yetkisiz erişim!"})

    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        # Müşteri bilgilerini al
        cursor.execute("SELECT * FROM Customers WHERE UserID = %s", (session['user_id'],))
        customer_info = cursor.fetchone()
        
        current_time = datetime.now()
        priority_score = calculate_priority_score(customer, current_time)
        
        return jsonify({
            "success": True,
            "customer_name": customer_info['CustomerName'],
            "customer_type": customer_info['CustomerType'],
            "customer_budget": customer_info['Budget'],
            "customer_budget": f"{customer['Budget']:.2f} TL",
            "priority_score": customer['PriorityScore'],
            "waiting_time": customer.get('WaitingTime', 'Hesaplanıyor...')
         #   "priority_score": priority_score
        })

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
    finally:
        cursor.close()
        conn.close()

@app.route('/customer-panel', methods=['GET'])
def customer_panel():
    if 'role' not in session or session['role'] != 'Customer':
        return redirect(url_for('login'))

    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        # Müşteri bilgilerini al
        cursor.execute("SELECT * FROM Customers WHERE UserID = %s", (session['user_id'],))
        customer_info = cursor.fetchone()

        # Ürünleri al
        cursor.execute("SELECT * FROM Products")
        products = cursor.fetchall()

        # Sepeti al
        cursor.execute("""
            SELECT p.ProductName, c.Quantity, c.TotalPrice, c.ProductID
            FROM Cart c
            JOIN Products p ON c.ProductID = p.ProductID
            WHERE c.CustomerID = %s
        """, (session['customer_id'],))
        cart = cursor.fetchall()

        # Toplam tutarı hesapla
        total_price = sum(item['TotalPrice'] for item in cart if item['TotalPrice'] is not None)

        # Kullanıcının siparişlerini al
        cursor.execute("""
            SELECT o.OrderID, p.ProductName, o.Quantity, o.OrderStatus
            FROM Orders o
            JOIN Products p ON o.ProductID = p.ProductID
            WHERE o.CustomerID = %s
        """, (session['customer_id'],))
        orders = cursor.fetchall()
        
        priority_score = calculate_priority_score(customer_info) 

        return render_template(
            'customer_panel.html',
            customer_info=customer_info,
            products=products,
            cart=cart,
            total_price=f"{total_price:.2f} TL",
            orders=orders,
            priority_score=priority_score
        )

    except Exception as e:
        error_message = f"Müşteri paneli hatası: {e}"
        print(traceback.format_exc())
        log_action(session['user_id'], "Error", error_message)
        return render_template('error.html', error=error_message)

    finally:
        cursor.close()
        conn.close()

def calculate_priority_score(customer_info):
    """Müşteri öncelik skorunu hesaplayan örnek fonksiyon."""
    budget = customer_info.get('Budget', 0)
    customer_type = customer_info.get('CustomerType', 'Normal')
    base_score = 10 if customer_type == 'Premium' else 5
    return base_score + budget // 1000  # Örnek hesaplama

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Kullanıcı oturumu yok!"})

    try:
        product_id = int(request.form['product_id'])
        quantity = int(request.form['quantity'])
        customer_id = session['customer_id']

        conn = get_database_connection()
        cursor = conn.cursor()

        # Ürün bilgilerini kontrol et
        cursor.execute("SELECT Stock, Price FROM Products WHERE ProductID = %s", (product_id,))
        product = cursor.fetchone()

        if not product:
            return jsonify({"success": False, "error": "Ürün bulunamadı!"})

        # Sepetteki mevcut ürün miktarını al
        cursor.execute("SELECT Quantity FROM Cart WHERE CustomerID = %s AND ProductID = %s", (customer_id, product_id))
        cart_item = cursor.fetchone()
        current_quantity = cart_item['Quantity'] if cart_item else 0

        # Stok kontrolü
        if product['Stock'] < (quantity + current_quantity):
            return jsonify({"success": False, "error": "Stok yetersiz!"})

        # Maksimum 5 adet kontrolü
        if (quantity + current_quantity) > 5:
            return jsonify({"success": False, "error": "Aynı üründen en fazla 5 adet ekleyebilirsiniz!"})

        total_price = product['Price'] * (quantity + current_quantity)

        if cart_item:
            # Mevcut ürünü güncelle
            cursor.execute("""
                UPDATE Cart
                SET Quantity = %s, TotalPrice = %s
                WHERE CustomerID = %s AND ProductID = %s
            """, ((quantity + current_quantity), total_price, customer_id, product_id))
        else:
            # Yeni ürün ekle
            cursor.execute("""
                INSERT INTO Cart (CustomerID, ProductID, Quantity, TotalPrice)
                VALUES (%s, %s, %s, %s)
            """, (customer_id, product_id, quantity, total_price))

        conn.commit()

        # Güncel sepeti al
        cursor.execute("""
            SELECT p.ProductName, c.Quantity, c.TotalPrice, c.ProductID
            FROM Cart c
            JOIN Products p ON c.ProductID = p.ProductID
            WHERE c.CustomerID = %s
        """, (customer_id,))
        cart_items = cursor.fetchall()
        conn.close()

        # Toplam tutarı hesapla
        total_price = sum(item['TotalPrice'] for item in cart_items)

        # Güncellenmiş sepet HTML'ini döndür
        cart_html = render_template("cart_section.html", cart=cart_items, total_price=f"{total_price:.2f} TL")
        return jsonify({"success": True, "cart_html": cart_html, "total_price": f"{total_price:.2f} TL"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})




@app.route('/remove-from-cart', methods=['POST'])
def remove_from_cart():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Kullanıcı oturumu yok!"})

    try:
        product_id = int(request.form['product_id'])
        customer_id = session['customer_id']

        conn = get_database_connection()
        cursor = conn.cursor()

        # Sepetten ürünü sil veya miktarı azalt
        cursor.execute("SELECT Quantity FROM Cart WHERE CustomerID = %s AND ProductID = %s", (customer_id, product_id))
        cart_item = cursor.fetchone()

        if not cart_item:
            return jsonify({"success": False, "error": "Geçersiz ürün ID!"})

        if cart_item['Quantity'] > 1:
            cursor.execute("""
                UPDATE Cart
                SET Quantity = Quantity - 1, TotalPrice = TotalPrice - (SELECT Price FROM Products WHERE ProductID = %s)
                WHERE CustomerID = %s AND ProductID = %s
            """, (product_id, customer_id, product_id))
        else:
            cursor.execute("DELETE FROM Cart WHERE CustomerID = %s AND ProductID = %s", (customer_id, product_id))

        conn.commit()

        # Sepet ve toplam fiyatı güncelle
        cursor.execute("""
            SELECT p.ProductName, c.Quantity, c.TotalPrice, c.ProductID
            FROM Cart c
            JOIN Products p ON c.ProductID = p.ProductID
            WHERE c.CustomerID = %s
        """, (customer_id,))
        cart = cursor.fetchall()

        total_price = sum(item['TotalPrice'] for item in cart)

        cart_html = render_template("cart_section.html", cart=cart, total_price=f"{total_price:.2f} TL")
        return jsonify({"success": True, "cart_html": cart_html})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

    finally:
        cursor.close()
        conn.close()



# Admin Paneli
@app.route('/admin-panel', methods=['GET'])
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

        # Siparişleri çek
        cursor.execute("""
            SELECT o.OrderID, c.CustomerName, p.ProductName, o.Quantity, o.TotalPrice, o.OrderStatus
            FROM Orders o
            JOIN Customers c ON o.CustomerID = c.CustomerID
            JOIN Products p ON o.ProductID = p.ProductID
        """)
        orders = cursor.fetchall()

        # Müşterileri çek
        cursor.execute("""
            SELECT CustomerID, CustomerName, Budget, TotalSpent, CustomerType, PriorityScore
            FROM Customers
        """)
        customers = cursor.fetchall()

        # Logları çek
        cursor.execute("""
            SELECT LogID, CustomerID, LogType, LogDetails, LogDate
            FROM Logs
            ORDER BY LogDate DESC
        """)
        logs = cursor.fetchall()

        conn.close()

        return render_template(
            'admin_panel.html',
            products=products,
            critical_products=critical_products,
            orders=orders,
            customers=customers,
            logs=logs
        )
    
    except Exception as e:
        log_action(session.get('user_id'), "Error", f"Admin panel hatası: {str(e)}")
        return f"Hata: {e}", 500

@app.route('/admin/approve-order', methods=['POST'])
def approve_order():
    """
    Sipariş onayı, bekleme süresi hesaplama ve öncelik skorunu güncelleme.
    """
    order_id = request.form.get('order_id')

    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        # Siparişin detaylarını al
        cursor.execute("SELECT * FROM Orders WHERE OrderID = %s", (order_id,))
        order = cursor.fetchone()

        if not order:
            return jsonify({"success": False, "error": "Sipariş bulunamadı!"})

        if order['OrderStatus'] == 'Tamamlandı':
            return jsonify({"success": False, "error": "Sipariş zaten onaylanmış."})

        # Onay zamanı
        approval_time = datetime.now()

        # Bekleme süresini hesapla
        order_date = order['OrderDate']
        waiting_time_seconds = (approval_time - order_date).total_seconds()

        # Sipariş durumunu ve onay zamanını güncelle
        cursor.execute("""
            UPDATE Orders
            SET OrderStatus = 'Tamamlandı', ApprovalDate = %s
            WHERE OrderID = %s
        """, (approval_time, order_id))

        # Öncelik skoru için müşteri bilgilerini al
        cursor.execute("SELECT * FROM Customers WHERE CustomerID = %s", (order['CustomerID'],))
        customer = cursor.fetchone()

        if not customer:
            return jsonify({"success": False, "error": "Müşteri bulunamadı!"})

        # Öncelik skoru hesaplama
        base_priority_score = 15 if customer['CustomerType'] == 'Premium' else 10
        waiting_time_weight = 0.5  # Her bir saniye bekleme ağırlığı
        new_priority_score = base_priority_score + (waiting_time_seconds * waiting_time_weight)

        # Öncelik skorunu güncelle
        cursor.execute("""
            UPDATE Customers
            SET PriorityScore = %s
            WHERE CustomerID = %s
        """, (new_priority_score, customer['CustomerID']))

        # Log kaydı oluştur
        log_message = (
            f"Sipariş {order_id} onaylandı. Bekleme süresi: {waiting_time_seconds} saniye. "
            f"Yeni öncelik skoru: {new_priority_score:.2f}"
        )
        log_action(order['CustomerID'], "Bilgilendirme", log_message)

        conn.commit()

        return jsonify({"success": True, "message": "Sipariş onaylandı!", "waiting_time": waiting_time_seconds})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

    finally:
        cursor.close()
        conn.close()


# Ürün Ekleme
@app.route('/admin/products/add', methods=['POST'])
def admin_add_product():
    if 'role' not in session or session['role'] != 'Admin':
        return "Yetkiniz yok!", 403

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
        log_action(None, "Info", f"Ürün eklendi: {product_name}, Stok: {stock}, Fiyat: {price}")
        return redirect(url_for('admin_panel'))
    except Exception as e:
        log_action(session.get('user_id'), "Error", f"Ürün ekleme hatası: {str(e)}")
        return f"Hata: {e}", 500


# Ürün Silme
@app.route('/admin/products/delete', methods=['POST'])
def admin_delete_product():
    if 'role' not in session or session['role'] != 'Admin':
        return "Yetkiniz yok!", 403

    product_id = int(request.form['product_id'])

    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Products WHERE ProductID = %s", (product_id,))
        conn.commit()
        conn.close()
        log_action(None, "Warning", f"Ürün silindi: ProductID={product_id}")
        return redirect(url_for('admin_panel'))
    except Exception as e:
        return f"Hata: {e}", 500


# Ürün Stok Güncelleme
@app.route('/admin/products/update', methods=['POST'])
def admin_update_product_stock():
    if 'role' not in session or session['role'] != 'Admin':
        return "Yetkiniz yok!", 403

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
        log_action(None, "Info", f"Ürün stoğu güncellendi: ProductID={product_id}, Yeni Stok: {new_stock}")
        return redirect(url_for('admin_panel'))
    except Exception as e:
        return f"Hata: {e}", 500


# Sipariş Onayı
@app.route('/admin/orders/approve', methods=['POST'])
def admin_approve_orders():
    if 'role' not in session or session['role'] != 'Admin':
        return "Yetkiniz yok!", 403

    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        # Bekleyen siparişleri onayla
        cursor.execute("""
            UPDATE Orders
            SET OrderStatus = 'Approved'
            WHERE OrderStatus = 'Pending'
        """)
        conn.commit()

        # Onaylanan siparişleri logla
        log_action(None, "Info", "Tüm bekleyen siparişler onaylandı.")
        conn.close()
        return redirect(url_for('admin_panel'))
    except Exception as e:
        return f"Hata: {e}", 500


# Logları Filtreleme
@app.route('/admin/logs', methods=['POST'])
def filter_logs():
    log_type = request.form['log_type']

    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        if log_type == "All":
            cursor.execute("SELECT * FROM Logs ORDER BY LogDate DESC")
        else:
            cursor.execute("SELECT * FROM Logs WHERE LogType = %s ORDER BY LogDate DESC", (log_type,))

        logs = cursor.fetchall()
        conn.close()

        return render_template('admin_panel.html', logs=logs)
    except Exception as e:
        return f"Hata: {e}", 500
# Dinamik Öncelik Yönetimi

def calculate_priority_score(customer_id):
    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        # Bekleyen siparişlerin bekleme süresini hesapla
        cursor.execute("""
            SELECT TIMESTAMPDIFF(MINUTE, o.OrderDate, NOW()) AS WaitingTime
            FROM Orders o
            WHERE o.CustomerID = %s AND o.OrderStatus = 'Pending'
        """, (customer_id,))
        waiting_times = cursor.fetchall()

        # Müşterinin toplam harcamalarını al
        cursor.execute("""
            SELECT SUM(TotalPrice) AS TotalSpent
            FROM Orders
            WHERE CustomerID = %s
        """, (customer_id,))
        total_spent = cursor.fetchone()['TotalSpent'] or 0

        # Öncelik skoru formülü
        priority_score = 10  # Varsayılan temel öncelik
        priority_score += sum(waiting_time['WaitingTime'] for waiting_time in waiting_times) * 0.1
        priority_score += total_spent * 0.05

        # Öncelik skorunu müşteriye kaydet
        cursor.execute("""
            UPDATE Customers
            SET PriorityScore = %s
            WHERE CustomerID = %s
        """, (priority_score, customer_id))
        conn.commit()
        conn.close()

    except Exception as e:
        print(f"Öncelik skoru hesaplanırken hata: {e}")

@app.route('/admin/logs', methods=['POST'])
def admin_logs():
    log_type = request.form.get('log_type', 'All')
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        if log_type == "All":
            cursor.execute("SELECT * FROM Logs ORDER BY LogDate DESC")
        else:
            cursor.execute("SELECT * FROM Logs WHERE LogType = %s ORDER BY LogDate DESC", (log_type,))
        
        logs = cursor.fetchall()
        conn.close()
        return render_template('admin_panel.html', logs=logs, log_filter=log_type)
    except Exception as e:
        return f"Hata: {e}", 500
    
@app.route('/products', methods=['GET'])
def get_products():
    """Tüm ürünleri listele."""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT ProductID, ProductName, Stock, Price FROM Products")
        products = cursor.fetchall()

        product_list = [
            {
                "ProductID": p[0],
                "ProductName": p[1],
                "Stock": p[2],
                "Price": float(p[3])
            }
            for p in products
        ]

        return jsonify({"success": True, "products": product_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
@app.route('/cart/add', methods=['POST'])
def api_add_to_cart():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Kullanıcı oturumu yok!"})

    try:
        customer_id = session['user_id']
        product_id = int(request.form['product_id'])
        quantity = int(request.form['quantity'])

        conn = get_database_connection()
        cursor = conn.cursor()

        # Ürün kontrolü
        cursor.execute("SELECT Stock, Price FROM Products WHERE ProductID = %s", (product_id,))
        product = cursor.fetchone()
        if not product:
            return jsonify({"success": False, "error": "Ürün bulunamadı!"})

        if product[0] < quantity:
            return jsonify({"success": False, "error": "Stok yetersiz!"})

        total_price = product[1] * quantity

        # Sepet güncelleme
        cursor.execute("""
            INSERT INTO Cart (CustomerID, ProductID, Quantity, TotalPrice)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            Quantity = Quantity + VALUES(Quantity),
            TotalPrice = TotalPrice + VALUES(TotalPrice)
        """, (customer_id, product_id, quantity, total_price))
        conn.commit()

        # Güncel sepeti çek
        cursor.execute("""
            SELECT p.ProductName, c.Quantity, c.TotalPrice
            FROM Cart c
            JOIN Products p ON c.ProductID = p.ProductID
            WHERE c.CustomerID = %s
        """, (customer_id,))
        cart_items = cursor.fetchall()
        conn.close()

        # Güncel sepet HTML'i döndür
        cart_html = render_template("cart_section.html", cart=cart_items)
        return jsonify({"success": True, "cart_html": cart_html})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
@app.route('/cart/view', methods=['GET'])
def view_cart():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Kullanıcı oturumu yok!"})

    try:
        customer_id = session['user_id']

        conn = get_database_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.ProductName, c.Quantity, c.TotalPrice
            FROM Cart c
            JOIN Products p ON c.ProductID = p.ProductID
            WHERE c.CustomerID = %s
        """, (customer_id,))
        cart_items = cursor.fetchall()
        conn.close()

        cart_list = []
        for item in cart_items:
            cart_list.append({
                "ProductName": item[0],
                "Quantity": item[1],
                "TotalPrice": float(item[2])
            })

        return jsonify({"success": True, "cart": cart_list})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})
    
@app.route('/cart/checkout', methods=['POST'])
def checkout_cart():
    if 'user_id' not in session:
        return jsonify({"success": False, "error": "Kullanıcı oturumu yok!"})

    try:
        customer_id = session['customer_id']

        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Sepet toplamını al
        cursor.execute("SELECT SUM(TotalPrice) AS CartTotal FROM Cart WHERE CustomerID = %s", (customer_id,))
        cart_total = cursor.fetchone()['CartTotal']

        # Müşteri bütçesini kontrol et
        cursor.execute("SELECT Budget FROM Customers WHERE CustomerID = %s", (customer_id,))
        budget = cursor.fetchone()['Budget']

        if cart_total > budget:
            return jsonify({"success": False, "error": "Bütçenizi aşıyor, lütfen sepeti güncelleyin!"})

        # Sepeti al
        cursor.execute("""
            SELECT ProductID, Quantity, TotalPrice
            FROM Cart
            WHERE CustomerID = %s
        """, (customer_id,))
        cart_items = cursor.fetchall()

        if not cart_items:
            return jsonify({"success": False, "error": "Sepet boş!"})

        # Sipariş oluştur
        for item in cart_items:
            cursor.execute("""
                INSERT INTO Orders (CustomerID, ProductID, Quantity, TotalPrice, OrderStatus)
                VALUES (%s, %s, %s, %s, 'Pending')
            """, (customer_id, item['ProductID'], item['Quantity'], item['TotalPrice']))
        
        cursor.execute("""
            UPDATE Customers
            SET LastOrderDate = NOW()
            WHERE CustomerID = %s
        """, (customer_id,))

        # Sepeti temizle (stok düşülmeden)
        cursor.execute("DELETE FROM Cart WHERE CustomerID = %s", (customer_id,))
        conn.commit()
        conn.close()

        log_action(customer_id, "Info", "Sipariş başarıyla oluşturuldu ve admin onayı bekliyor.")
        return jsonify({"success": True, "message": "Sipariş oluşturuldu, admin onayı bekleniyor!"})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

    
# Tüm isteklerin loglanması
@app.after_request
def log_request(response):
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        log_type = "Info" if response.status_code == 200 else "Error"
        log_details = f"Path: {request.path}, Status: {response.status_code}, Method: {request.method}"
        cursor.execute("""
            INSERT INTO Logs (CustomerID, LogType, LogDetails, LogDate)
            VALUES (%s, %s, %s, NOW())
        """, (session.get('user_id'), log_type, log_details))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"After request loglama hatası: {e}")
    return response

@app.route('/cleanup-cart', methods=['POST'])
def cleanup_cart():
    customer.remove_expired_cart_items()
    return jsonify({"success": True, "message": "Eski sepet ürünleri temizlendi."})


# Çıkış Yapma
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def home():
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
