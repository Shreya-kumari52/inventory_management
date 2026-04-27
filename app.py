from flask import Flask, render_template, request, redirect, session, send_from_directory
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = "secret123"

# DB connection
def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root@123",
        database="inventory_db",
        autocommit=True   # 🔥 performance improve
    )

# 🔥 IMPORTANT FIX (static/uploads use करो)
UPLOAD_FOLDER = os.path.join("static", "uploads")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# LOGIN
@app.route('/', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s",(username,password))
        user = cursor.fetchone()

        cursor.close()
        db.close()

        if user:
            session['user'] = username
            return redirect('/dashboard')
        else:
            error = "Invalid ID or Password"

    return render_template('login.html', error=error)

# DASHBOARD
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/')
    return render_template('dashboard.html')

# ITEMS
@app.route('/items')
def items():
    if 'user' not in session:
        return redirect('/')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    search = request.args.get('search', '')
    category = request.args.get('category', '')

    # 🔥 IMPROVED QUERY
    query = "SELECT * FROM items WHERE 1=1"
    params = []

    if search:
        query += " AND name LIKE %s"
        params.append(f"%{search}%")

    if category:
        query += " AND category=%s"
        params.append(category)

    cursor.execute(query, params)
    data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template('items.html', items=data)

# ADD ITEM
@app.route('/add', methods=['GET','POST'])
def add():
    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        weight = request.form['weight']
        purchase = request.form['purchase']
        selling = request.form['selling']
        quality = request.form['quality']

        file = request.files['image']
        filename = file.filename if file else ""

        if filename:
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO items(name,category,weight,purchase_price,selling_price,quality,image)
            VALUES(%s,%s,%s,%s,%s,%s,%s)
        """,(name,category,weight,purchase,selling,quality,filename))

        cursor.close()
        db.close()

        return redirect('/items')

    return render_template('add_edit.html', item=None)

# EDIT ITEM
@app.route('/edit/<int:id>', methods=['GET','POST'])
def edit(id):
    if 'user' not in session:
        return redirect('/')

    db = get_db()
    cursor = db.cursor(dictionary=True)

    if request.method == 'POST':
        name = request.form['name']
        category = request.form['category']
        weight = request.form['weight']
        purchase = request.form['purchase']
        selling = request.form['selling']
        quality = request.form['quality']

        file = request.files['image']
        filename = file.filename if file else ""

        if filename:
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            cursor.execute("""
                UPDATE items SET name=%s, category=%s, weight=%s,
                purchase_price=%s, selling_price=%s,
                quality=%s, image=%s WHERE id=%s
            """,(name,category,weight,purchase,selling,quality,filename,id))
        else:
            cursor.execute("""
                UPDATE items SET name=%s, category=%s, weight=%s,
                purchase_price=%s, selling_price=%s,
                quality=%s WHERE id=%s
            """,(name,category,weight,purchase,selling,quality,id))

        cursor.close()
        db.close()

        return redirect('/items')

    cursor.execute("SELECT * FROM items WHERE id=%s",(id,))
    item = cursor.fetchone()

    cursor.close()
    db.close()

    return render_template('add_edit.html', item=item)

# DELETE
@app.route('/delete/<int:id>')
def delete(id):
    if 'user' not in session:
        return redirect('/')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("DELETE FROM items WHERE id=%s",(id,))

    cursor.close()
    db.close()

    return redirect('/items')

# IMAGE SHOW (अब static use हो रहा है, ये optional है)
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# LOGOUT
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)