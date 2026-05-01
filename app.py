from flask import Flask, render_template, request, redirect, session, send_from_directory
import psycopg
from psycopg.rows import dict_row
import os
import traceback

app = Flask(__name__)
app.secret_key = "secret123"

# ✅ DEBUG
app.config['PROPAGATE_EXCEPTIONS'] = True


# ================= DATABASE ================= #

def get_db():
    try:
        db_url = os.getenv("DATABASE_URL")

        conn = psycopg.connect(db_url)

        return conn

    except Exception as e:
        print("DB ERROR:", e)
        return None


# ================= UPLOAD ================= #

UPLOAD_FOLDER = os.path.join("static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ================= INIT DB ================= #

def init_db():
    db = get_db()

    if db is None:
        print("❌ DB not connected")
        return

    try:
        cursor = db.cursor(row_factory=dict_row)

        # USERS TABLE
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
        """)

        # ITEMS TABLE
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
        cursor.execute("""
        INSERT INTO users (username,password)
        VALUES ('deepak','deepak123')
        ON CONFLICT (username) DO NOTHING
        """)

        cursor.execute("""
        INSERT INTO users (username,password)
        VALUES ('raushan','raushan123')
        ON CONFLICT (username) DO NOTHING
        """)

        cursor.execute("""
        INSERT INTO users (username,password)
        VALUES ('naman','naman123')
        ON CONFLICT (username) DO NOTHING
        """)

        db.commit()

        print("✅ DATABASE INITIALIZED")

        cursor.close()
        db.close()

    except Exception as e:
        print("❌ INIT DB ERROR:", e)
        traceback.print_exc()


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

        username = request.form.get('username')
        password = request.form.get('password')

        db = get_db()

        if db is None:
            return "Database connection failed ❌"

        try:
            cursor = db.cursor(row_factory=dict_row)

            cursor.execute(
                "SELECT * FROM users WHERE username=%s AND password=%s",
                (username, password)
            )

            user = cursor.fetchone()

            cursor.close()
            db.close()

            if user:
                session['user'] = username
                return redirect('/dashboard')

            else:
                error = "Invalid ID or Password"

        except Exception as e:
            print("❌ LOGIN ERROR:", e)
            traceback.print_exc()
            return f"<pre>{traceback.format_exc()}</pre>"

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
        return "Database connection failed ❌"

    try:
        cursor = db.cursor(row_factory=dict_row)

        cursor.execute("""
        SELECT * FROM items
        ORDER BY id DESC
        """)

        data = cursor.fetchall()

        cursor.close()
        db.close()

    except Exception as e:
        print("❌ ITEMS ERROR:", e)
        traceback.print_exc()
        data = []

    return render_template(
        'items.html',
        items=data,
        page=1,
        total_pages=1,
        search="",
        category=""
    )


# ADD ITEM
@app.route('/add', methods=['GET', 'POST'])
def add():

    if 'user' not in session:
        return redirect('/')

    if request.method == 'POST':

        try:
            name = request.form.get('name')
            category = request.form.get('category')
            weight = request.form.get('weight')
            quality = request.form.get('quality')

            # SAFE FLOAT
            try:
                purchase = float(request.form.get('purchase', 0))
            except:
                purchase = 0

            filename = ""

            # IMAGE
            file = request.files.get('image')

            if file and file.filename != "":

                try:
                    filename = file.filename

                    save_path = os.path.join(UPLOAD_FOLDER, filename)

                    file.save(save_path)

                    print("✅ IMAGE SAVED:", save_path)

                except Exception as e:
                    print("❌ IMAGE SAVE ERROR:", e)
                    filename = ""

            db = get_db()

            if db is None:
                return "Database connection failed ❌"

            cursor = db.cursor(row_factory=dict_row)

            cursor.execute("""
                INSERT INTO items
                (name,category,weight,purchase_price,quality,image)
                VALUES(%s,%s,%s,%s,%s,%s)
            """, (
                name,
                category,
                weight,
                purchase,
                quality,
                filename
            ))

            db.commit()

            print("✅ ITEM INSERTED")

            cursor.close()
            db.close()

            return redirect('/items')

        except Exception as e:
            print("❌ ADD ERROR:", e)
            traceback.print_exc()

            return f"<pre>{traceback.format_exc()}</pre>"

    return render_template('add_edit.html', item=None)


# DELETE
@app.route('/delete/<int:id>')
def delete(id):

    if 'user' not in session:
        return redirect('/')

    db = get_db()

    if db is None:
        return "Database connection failed ❌"

    try:
        cursor = db.cursor(row_factory=dict_row)

        cursor.execute(
            "DELETE FROM items WHERE id=%s",
            (id,)
        )

        db.commit()

        cursor.close()
        db.close()

        print("✅ ITEM DELETED")

    except Exception as e:
        print("❌ DELETE ERROR:", e)
        traceback.print_exc()

    return redirect('/items')


# LOGOUT
@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect('/')


# IMAGE
@app.route('/uploads/<filename>')
def uploaded_file(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


# RUN LOCAL
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000,
        debug=True
    )