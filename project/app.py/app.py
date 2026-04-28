from flask import Flask, request, redirect, session, render_template_string, jsonify, g
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret123"
DATABASE = "food.db"

# ---------------- DATABASE ----------------
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

with sqlite3.connect(DATABASE) as con:
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY, username TEXT, items TEXT)")

# ---------------- MENU ----------------
menu = [
    {"name": "Cold Coffee", "price": 100},
    {"name": "Sandwich", "price": 80},
    {"name": "Pizza", "price": 200},
    {"name": "Burger", "price": 120}
]

# ---------------- UI PAGES ----------------
@app.route('/')
def home():
    if 'user' not in session:
        return redirect('/login_page')

    return render_template_string("""
    <html>
    <head>
    <style>
        body{background:#111;color:white;font-family:Arial;margin:0}
        .nav{background:#ff4d4d;padding:15px;display:flex;justify-content:space-between}
        .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;padding:20px}
        .card{background:#222;padding:15px;border-radius:15px;text-align:center}
        button{background:#ff4d4d;border:none;padding:10px;border-radius:8px;color:white;cursor:pointer}
        a{color:white;text-decoration:none}
    </style>
    </head>
    <body>
        <div class="nav">
            <h2>Zynex 🍔</h2>
            <div>
                {{user}} | <a href="/cart_page">Cart</a> | <a href="/orders_page">Orders</a> | <a href="/logout">Logout</a>
            </div>
        </div>

        <div class="grid">
        {% for item in menu %}
            <div class="card">
                <h3>{{item.name}}</h3>
                <p>₹{{item.price}}</p>
                <a href="/add/{{item.name}}"><button>Add to Cart</button></a>
            </div>
        {% endfor %}
        </div>
    </body>
    </html>
    """, menu=menu, user=session['user'])

@app.route('/login_page')
def login_page():
    return render_template_string("""
    <body style='background:#111;color:white;text-align:center'>
    <h2>Login</h2>
    <form method='post' action='/login'>
    <input name='username' placeholder='Username'><br><br>
    <input name='password' type='password' placeholder='Password'><br><br>
    <button>Login</button>
    </form>
    <a href='/signup_page'>Signup</a>
    </body>
    """)

@app.route('/signup_page')
def signup_page():
    return render_template_string("""
    <body style='background:#111;color:white;text-align:center'>
    <h2>Signup</h2>
    <form method='post' action='/signup'>
    <input name='username' placeholder='Username'><br><br>
    <input name='password' type='password' placeholder='Password'><br><br>
    <button>Signup</button>
    </form>
    </body>
    """)

@app.route('/cart_page')
def cart_page():
    cart = session.get('cart', [])
    return render_template_string("""
    <body style='background:#111;color:white;text-align:center'>
    <h2>Cart</h2>
    {% for item in cart %}
        <p>{{item}}</p>
    {% endfor %}
    <a href='/order'><button>Place Order</button></a><br><br>
    <a href='/'>Back</a>
    </body>
    """, cart=cart)

@app.route('/orders_page')
def orders_page():
    db = get_db()
    cur = db.execute("SELECT items FROM orders WHERE username=?", (session['user'],))
    data = cur.fetchall()
    return render_template_string("""
    <body style='background:#111;color:white;text-align:center'>
    <h2>Your Orders</h2>
    {% for row in data %}
        <p>{{row[0]}}</p>
    {% endfor %}
    <a href='/'>Back</a>
    </body>
    """, data=data)

# ---------------- AUTH ----------------
@app.route('/signup', methods=['POST'])
def signup():
    db = get_db()
    hashed = generate_password_hash(request.form['password'])
    try:
        db.execute("INSERT INTO users (username,password) VALUES (?,?)",
                   (request.form['username'], hashed))
        db.commit()
        return redirect('/login_page')
    except:
        return "User exists"

@app.route('/login', methods=['POST'])
def login():
    db = get_db()
    cur = db.execute("SELECT password FROM users WHERE username=?", (request.form['username'],))
    user = cur.fetchone()

    if user and check_password_hash(user[0], request.form['password']):
        session['user'] = request.form['username']
        session['cart'] = []
        return redirect('/')
    return "Invalid login"

# ---------------- CART ----------------
@app.route('/add/<item>')
def add(item):
    session['cart'].append(item)
    session.modified = True
    return redirect('/')

# ---------------- ORDER ----------------
@app.route('/order')
def order():
    db = get_db()
    items = ",".join(session.get('cart', []))
    db.execute("INSERT INTO orders (username,items) VALUES (?,?)",
               (session['user'], items))
    db.commit()
    session['cart'] = []
    return redirect('/orders_page')

# ---------------- API ----------------
@app.route('/menu')
def api_menu():
    return jsonify(menu)

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login_page')

# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)
    