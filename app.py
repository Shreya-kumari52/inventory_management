from flask import Flask, render_template, request, redirect, session, send_from_directory
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

# DB connection (SQLite)
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# UPLOAD FOLDER
UPLOAD_FOLDER = os.path.join("static", "uploads")

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# 🔥 AUTO CREATE DATABASE (ONLY ONE FUNCTION)
def init_db():
    db = get_db()
    cursor = db.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # ITEMS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        weight TEXT,
        purchase_price REAL,
        selling_price REAL,
        quality TEXT,
        image TEXT
    )
    """)

    # DEFAULT USERS
    cursor.execute("INSERT OR IGNORE INTO users (username,password) VALUES ('deepak','deepak123')")
    cursor.execute("INSERT OR IGNORE INTO users (username,password) VALUES ('raushan','raushan123')")
    cursor.execute("INSERT OR IGNORE INTO users (username,password) VALUES ('naman','naman123')")

    db.commit()
    db.close()

# CALL INIT
init_db()

# LOGIN
@app.route('/', methods=['GET','POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()

        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
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

# ITEMS (PAGINATION + SEARCH)
@app.route('/items')
def items():
    if 'user' not in session:
        return redirect('/')

    db = get_db()
    cursor = db.cursor()

    search = request.args.get('search', '')
    category = request.args.get('category', '')
    page = request.args.get('page', 1, type=int)

    limit = 12
    offset = (page - 1) * limit

    query = "SELECT * FROM items WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR category LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    if category:
        query += " AND category=?"
        params.append(category)

    # COUNT QUERY
    count_query = "SELECT COUNT(*) FROM items WHERE 1=1"
    count_params = []

    if search:
        count_query += " AND (name LIKE ? OR category LIKE ?)"
        count_params.extend([f"%{search}%", f"%{search}%"])

    if category:
        count_query += " AND category=?"
        count_params.append(category)

    cursor.execute(count_query, count_params)
    total = cursor.fetchone()[0]

    # LIMIT
    query += " LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    data = cursor.fetchall()

    total_pages = (total // limit) + (1 if total % limit else 0)

    cursor.close()
    db.close()

    return render_template('items.html',
                           items=data,
                           page=page,
                           total_pages=total_pages,
                           search=search,
                           category=category)

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
            VALUES(?,?,?,?,?,?,?)
        """, (name, category, weight, purchase, selling, quality, filename))

        db.commit()
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
    cursor = db.cursor()

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
                UPDATE items SET name=?, category=?, weight=?,
                purchase_price=?, selling_price=?,
                quality=?, image=? WHERE id=?
            """, (name, category, weight, purchase, selling, quality, filename, id))
        else:
            cursor.execute("""
                UPDATE items SET name=?, category=?, weight=?,
                purchase_price=?, selling_price=?,
                quality=? WHERE id=?
            """, (name, category, weight, purchase, selling, quality, id))

        db.commit()
        cursor.close()
        db.close()

        return redirect('/items')

    cursor.execute("SELECT * FROM items WHERE id=?", (id,))
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

    cursor.execute("DELETE FROM items WHERE id=?", (id,))
    db.commit()

    cursor.close()
    db.close()

    return redirect('/items')

# IMAGE SHOW
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# LOGOUT
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# DEPLOY FIX
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)