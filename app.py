from flask import Flask, render_template, request, redirect, session
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

        conn = psycopg.connect(
            db_url,
            row_factory=dict_row
        )

        return conn

    except Exception as e:
        print("DB ERROR:", e)
        return None


# ================= INIT DB ================= #

def init_db():

    db = get_db()

    if db is None:
        print("❌ DB not connected")
        return

    try:
        cursor = db.cursor()

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
            quality TEXT
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
            cursor = db.cursor()

            cursor.execute(
                """
                SELECT * FROM users
                WHERE username=%s AND password=%s
                """,
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

    return render_template(
        'login.html',
        error=error
    )


# DASHBOARD
@app.route('/dashboard')
def dashboard():

    if 'user' not in session:
        return redirect('/')

    return render_template('dashboard.html')


# ================= ITEMS ================= #

@app.route('/items')
def items():

    if 'user' not in session:
        return redirect('/')

    db = get_db()

    if db is None:
        return "Database connection failed ❌"

    try:

        # 🔍 SEARCH
        search = request.args.get("search", "").strip()

        # 🔍 CATEGORY
        category = request.args.get("category", "").strip()

        cursor = db.cursor()

        query = """
        SELECT * FROM items
        WHERE 1=1
        """

        params = []

        # SEARCH FILTER
        if search:

            query += """
            AND LOWER(name) LIKE %s
            """

            params.append(f"%{search.lower()}%")

        # CATEGORY FILTER
        if category:

            query += """
            AND category=%s
            """

            params.append(category)

        query += """
        ORDER BY id DESC
        """

        cursor.execute(query, params)

        data = cursor.fetchall()

        cursor.close()
        db.close()

    except Exception as e:

        print("❌ ITEMS ERROR:", e)

        traceback.print_exc()

        data = []

        search = ""
        category = ""

    return render_template(
        'items.html',
        items=data,
        page=1,
        total_pages=1,
        search=search,
        category=category
    )


# ================= ADD ITEM ================= #

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
                purchase = float(
                    request.form.get('purchase', 0)
                )

            except:
                purchase = 0

            db = get_db()

            if db is None:
                return "Database connection failed ❌"

            cursor = db.cursor()

            # ✅ INSERT
            cursor.execute("""
                INSERT INTO items
                (
                    name,
                    category,
                    weight,
                    purchase_price,
                    quality
                )
                VALUES(%s,%s,%s,%s,%s)
            """, (
                name,
                category,
                weight,
                purchase,
                quality
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

    return render_template(
        'add_edit.html',
        item=None
    )



# EDIT ITEM
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):

    if 'user' not in session:
        return redirect('/')

    db = get_db()

    if db is None:
        return "Database connection failed ❌"

    cursor = db.cursor(row_factory=dict_row)

    # GET ITEM
    cursor.execute(
        "SELECT * FROM items WHERE id=%s",
        (id,)
    )

    item = cursor.fetchone()

    # UPDATE
    if request.method == 'POST':

        try:
            name = request.form.get('name')
            category = request.form.get('category')
            weight = request.form.get('weight')
            purchase = request.form.get('purchase')
            quality = request.form.get('quality')

            cursor.execute("""
                UPDATE items
                SET
                name=%s,
                category=%s,
                weight=%s,
                purchase_price=%s,
                quality=%s
                WHERE id=%s
            """, (
                name,
                category,
                weight,
                purchase,
                quality,
                id
            ))

            db.commit()

            cursor.close()
            db.close()

            print("✅ ITEM UPDATED")

            return redirect('/items')

        except Exception as e:
            print("❌ EDIT ERROR:", e)
            traceback.print_exc()

            return f"<pre>{traceback.format_exc()}</pre>"

    cursor.close()
    db.close()

    return render_template(
        'add_edit.html',
        item=item
    )

# ================= DELETE ================= #

@app.route('/delete/<int:id>')
def delete(id):

    if 'user' not in session:
        return redirect('/')

    db = get_db()

    if db is None:
        return "Database connection failed ❌"

    try:

        cursor = db.cursor()

        cursor.execute(
            """
            DELETE FROM items
            WHERE id=%s
            """,
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


# ================= LOGOUT ================= #

@app.route('/logout')
def logout():

    session.pop('user', None)

    return redirect('/')


# ================= RUN LOCAL ================= #

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000,
        debug=True
    )