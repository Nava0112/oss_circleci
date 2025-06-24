from flask import Flask, render_template, request, redirect, url_for, session
import cx_Oracle
import os
from datetime import datetime
import apminsight

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Database config
DB_USER = os.getenv("DB_USER", "system")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_DSN = os.getenv("DB_DSN", "host.docker.internal:1521/ORCL")

def get_db_connection():
    return cx_Oracle.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN)

# ------------------ CUSTOMER LOGIN ------------------
@app.route('/', methods=['GET', 'POST'])
def login_customer():
    if request.method == 'POST':
        customer_id = request.form['CustomerID']
        customer_name = request.form['CustomerName']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Customers WHERE CustomerID=:1 AND CustomerName=:2", (customer_id, customer_name))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user:
            session['customer_id'] = customer_id
            return redirect(url_for('products'))
        else:
            return "Invalid customer credentials"
    return render_template('login_customer.html')

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        data = (
            request.form['CustomerID'],
            request.form['CustomerName'],
            request.form['PhoneNumber'],
            request.form['Email'],
            request.form['Address']
        )
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Customers (CustomerID, CustomerName, PhoneNumber, Email, Address)
            VALUES (:1, :2, :3, :4, :5)
        """, data)
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('login_customer'))
    return render_template('add_customer.html')

# ------------------ SUPPLIER LOGIN ------------------
@app.route('/login_supplier', methods=['GET', 'POST'])
def login_supplier():
    if request.method == 'POST':
        try:
            supplier_id = int(request.form['SupplierID'])  # 🔧 Ensure correct type
            supplier_name = request.form['SupplierName'].strip().lower()  # 🔧 Clean input
        except ValueError:
            return "Invalid Supplier ID format"

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT * FROM Suppliers 
            WHERE SupplierID = :1 AND LOWER(TRIM(SupplierName)) = :2
        """, (supplier_id, supplier_name))  # 🔧 Case-insensitive name check
        supplier = cursor.fetchone()
        cursor.close()
        connection.close()

        if supplier:
            session['supplier_id'] = supplier_id
            return redirect(url_for('supplier_products'))
        else:
            return redirect(url_for('add_supplier'))

    return render_template('login_supplier.html')


@app.route('/add_supplier', methods=['GET', 'POST'])
def add_supplier():
    if request.method == 'POST':
        data = (
            request.form['SupplierID'],
            request.form['SupplierName'],
            request.form['PhoneNumber'],
            request.form['Email'],
            request.form['Address']
        )
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Suppliers (SupplierID, SupplierName, PhoneNumber, Email, Address)
            VALUES (:1, :2, :3, :4, :5)
        """, data)
        conn.commit()
        cursor.close()
        conn.close()
        session['supplier_id'] = data[0]  # log in the new supplier
        return redirect(url_for('add_product_by_supplier'))
    return render_template('add_supplier.html')

# ------------------ PRODUCTS ------------------
@app.route('/products')
def products():
    if 'customer_id' not in session:
        return redirect(url_for('login_customer'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/buy_product/<int:product_id>')
def buy_product(product_id):
    if 'customer_id' not in session:
        return redirect(url_for('login_customer'))
    order_id = int(datetime.now().timestamp())  # Unique order ID
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO Orders (OrderID, CustomerID, ProductID, Order_Date, Status)
        VALUES (:1, :2, :3, :4, :5)
    """, (order_id, session['customer_id'], product_id, datetime.now(), 'Pending'))
    cursor.execute("SELECT * FROM Products WHERE ProductID = :1", (product_id,))
    product = cursor.fetchone()
    conn.commit()
    cursor.close()
    conn.close()
    return render_template('order_confirmation.html', product=product)

# ------------------ SUPPLIER PRODUCTS ------------------
@app.route('/supplier_products')
def supplier_products():
    if 'supplier_id' not in session:
        return redirect(url_for('login_supplier'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Products WHERE SupplierID = :1", (session['supplier_id'],))
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('supplier_products.html', products=products)

@app.route('/add_product_by_supplier', methods=['GET', 'POST'])
def add_product_by_supplier():
    if 'supplier_id' not in session:
        return redirect(url_for('login_supplier'))
    if request.method == 'POST':
        data = (
            request.form['ProductID'],
            request.form['ProductName'],
            session['supplier_id'],
            request.form['Category'],
            float(request.form['UnitPrice']),
            int(request.form['QuantityInStock'])
        )
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Products (ProductID, ProductName, SupplierID, Category, UnitPrice, QuantityInStock)
            VALUES (:1, :2, :3, :4, :5, :6)
        """, data)
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('supplier_products'))
    return render_template('add_product_by_supplier.html')

# ------------------ LOGOUT ------------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_customer'))  # FIXED redirect

# ------------------ RUN APP ------------------
if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)

