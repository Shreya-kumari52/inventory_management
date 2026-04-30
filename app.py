from flask import Flask, render_template, request, redirect, session, send_from_directory
import psycopg
import os

app = Flask(__name__)
app.secret_key = "secret123"


# ================= DATABASE ================= #

def get_db():
    try:
        db_url = os.environ.get("DATABASE_URL")

        if not db_url:
            raise Exception("DATABASE_URL missing ❌")

        return psycopg.connect(db_url, sslmode="require")

    except Exception as e:
        print("DB CONNECTION ERROR:", e)
        return None


# ================= UPLOAD ================= #

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ================= INIT DB ================= #

def init_db():
    db = get_db()
    if db is None:
        print("DB not connected ❌")
        return

    try:
        cursor = db.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
        """)

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

        cursor.execute("INSERT INTO users (username,password) VALUES ('deepak','deepak123') ON CONFLICT DO NOTHING")
        cursor.execute("INSERT INTO users (username,password) VALUES ('raushan','raushan123') ON CONFLICT DO NOTHING")
        cursor.execute("INSERT INTO users (username,password) VALUES ('naman','naman123') ON CONFLICT DO NOTHING")

        db.commit()
        cursor.close()
        db.close()

    except Exception as e:
        print("INIT DB ERROR:", e)


# ✅ RUN ONLY ONCE
@app.before_request
def setup():
    if not hasattr(app, "db_initialized"):
        init_db()
        app.db_initialized = True


# ================= ROUTES ================= #

# LOGIN
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        if db is None:
            return "Database connection failed ❌"

        cursor = db.cursor()

        try:
            cursor.execute(
                "SELECT * FROM users WHERE username=%s AND password=%s",
                (username, password)
            )
            user = cursor.fetchone()

        except Exception as e:
            print("LOGIN ERROR:", e)
            user = None

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
    if db is None:
        return "Database error ❌"

    cursor = db.cursor()

    try:
        cursor.execute("SELECT * FROM items ORDER BY id DESC")
        data = cursor.fetchall()

    except Exception as e:
        print("ITEM ERROR:", e)
        data = []

    cursor.close()
    db.close()

    return render_template('items.html', items=data, page=1, total_pages=1)


# ADD ITEM
@app.route('/add', methods=['GET','POST'])
def add():
    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':
        try:
            name = request.form.get('name')
            category = request.form.get('category')
            weight = request.form.get('weight')
            quality = request.form.get('quality')

            purchase = request.form.get('purchase')
            purchase = float(purchase) if purchase else 0

            filename = ""

            # ❌ FILE IGNORE (for now to avoid crash)
            file = request.files.get('image')
            if file and file.filename != "":
                try:
                    filename = file.filename
                    file.save(os.path.join(UPLOAD_FOLDER, filename))
                except:
                    filename = ""

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

        except Exception as e:
            print("ADD ERROR:", e)
            return str(e)

    return render_template('add_edit.html', item=None)


# LOGOUT
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


# IMAGE
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)


# RUN LOCAL
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)