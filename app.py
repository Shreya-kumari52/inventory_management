from flask import Flask, render_template, request, redirect, session, send_from_directory
import psycopg
import os

app = Flask(__name__)
app.secret_key = "secret123"

# ✅ DATABASE CONNECTION (Supabase FIXED)
def get_db():
    return psycopg.connect(
        os.environ.get("DATABASE_URL"),
        sslmode="require"
    )

# UPLOAD FOLDER
UPLOAD_FOLDER = os.path.join("static", "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ✅ AUTO CREATE DATABASE
def init_db():
    db = get_db()
    cursor = db.cursor()

    # USERS TABLE
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password TEXT
    )
    """)

    # ITEMS TABLE (selling_price removed)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id SERIAL PRIMARY KEY,
        name TEXT,
        category TEXT,
        weight TEXT,
        purchase_price REAL,
        quality TEXT,
        image TEXT
    )
    """)

    # DEFAULT USERS
    cursor.execute("INSERT INTO users (username,password) VALUES ('deepak','deepak123') ON CONFLICT DO NOTHING")
    cursor.execute("INSERT INTO users (username,password) VALUES ('raushan','raushan123') ON CONFLICT DO NOTHING")
    cursor.execute("INSERT INTO users (username,password) VALUES ('naman','naman123') ON CONFLICT DO NOTHING")

    db.commit()
    cursor.close()
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

        cursor.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
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

# ITEMS (SEARCH + PAGINATION FIXED)
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
        query += " AND (name ILIKE %s OR category ILIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])

    if category:
        query += " AND category=%s"
        params.append(category)

    # ✅ COUNT QUERY FIXED
    count_query = "SELECT COUNT(*) FROM items WHERE 1=1"
    count_params = []

    if search:
        count_query += " AND (name ILIKE %s OR category ILIKE %s)"
        count_params.extend([f"%{search}%", f"%{search}%"])

    if category:
        count_query += " AND category=%s"
        count_params.append(category)

    cursor.execute(count_query, count_params)
    total = cursor.fetchone()[0]

    query += " LIMIT %s OFFSET %s"
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
        quality = request.form['quality']

        file = request.files['image']
        filename = file.filename if file else ""

        if filename:
            file.save(os.path.join(UPLOAD_FOLDER, filename))

        db = get_db()
        cursor = db.cursor()

        cursor.execute("""
            INSERT INTO items(name,category,weight,purchase_price,quality,image)
            VALUES(%s,%s,%s,%s,%s,%s)
        """, (name, category, weight, purchase, quality, filename))

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
        quality = request.form['quality']

        file = request.files['image']
        filename = file.filename if file else ""

        if filename:
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            cursor.execute("""
                UPDATE items SET name=%s, category=%s, weight=%s,
                purchase_price=%s, quality=%s, image=%s WHERE id=%s
            """, (name, category, weight, purchase, quality, filename, id))
        else:
            cursor.execute("""
                UPDATE items SET name=%s, category=%s, weight=%s,
                purchase_price=%s, quality=%s WHERE id=%s
            """, (name, category, weight, purchase, quality, id))

        db.commit()
        cursor.close()
        db.close()

        return redirect('/items')

    cursor.execute("SELECT * FROM items WHERE id=%s", (id,))
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

    cursor.execute("DELETE FROM items WHERE id=%s", (id,))
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

# RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)