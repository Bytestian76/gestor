from flask import Flask, render_template, request, redirect, session, flash, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = 'lunenauditore'

# --- Conexión a la base de datos ---
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# --- Crear tablas ---
def create_table():
    conn = get_db_connection()

    conn.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente TEXT NOT NULL,
            contacto TEXT NOT NULL,
            descripcion TEXT,
            fecha_entrega TEXT,
            estado TEXT,
            precio REAL
        )
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

# --- Registro ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        email = request.form.get('email')
        password = request.form.get('password')

        if not nombre or not email or not password:
            flash('Por favor completa todos los campos.')
            return redirect('/register')

        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)',
                         (nombre, email, password))
            conn.commit()
            flash('Cuenta creada correctamente. Ahora puedes iniciar sesión.')
            return redirect('/login')
        except sqlite3.IntegrityError:
            flash('El correo ya está registrado.')
            return redirect('/register')
        finally:
            conn.close()

    return render_template('register.html')

# --- Login ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        if not email or not password:
            flash('Por favor ingresa tu correo y contraseña.')
            return redirect('/login')

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM usuarios WHERE email = ? AND password = ?',
            (email, password)
        ).fetchone()
        conn.close()

        if user:
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_nombre'] = user['nombre'] 
            flash('Has iniciado sesión correctamente.')
            return redirect('/index')

        else:
            flash('Correo o contraseña incorrectos.')
            return redirect('/login')

    return render_template('login.html')

# --- Logout ---
@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.')
    return redirect('/login')

# --- Página principal (Index) ---
@app.route('/')
def home():
    return redirect('/index')

@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    nombre = session.get('user_nombre', 'Usuario')
    return render_template('index.html', nombre=nombre)


# --- Listado de pedidos ---
@app.route('/pedidos', methods=['GET', 'POST'])
def pedidos():
    if 'user_id' not in session:
        return redirect('/login')

    search = request.args.get('search', '').strip()  # Obtener término de búsqueda

    conn = get_db_connection()
    
    if search:
        query = '''
            SELECT * FROM pedidos 
            WHERE cliente LIKE ? 
               OR contacto LIKE ? 
               OR descripcion LIKE ? 
               OR estado LIKE ? 
               OR precio LIKE ?
        '''
        like_search = f"%{search}%"
        pedidos = conn.execute(query, (like_search, like_search, like_search, like_search, like_search)).fetchall()
    else:
        pedidos = conn.execute('SELECT * FROM pedidos').fetchall()

    conn.close()
    return render_template('pedidos.html', pedidos=pedidos, search=search)


# --- Agregar pedido ---
@app.route('/pedidos/agregar', methods=['GET', 'POST'])
def agregar():
    if 'user_id' not in session:
        return redirect('/login')

    if request.method == 'POST':
        cliente = request.form['cliente']
        contacto = request.form['contacto']
        descripcion = request.form['descripcion']
        fecha_entrega = request.form['fecha_entrega']
        estado = request.form['estado']
        precio = request.form['precio']

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO pedidos (cliente, contacto, descripcion, fecha_entrega, estado, precio) VALUES (?, ?, ?, ?, ?, ?)',
            (cliente, contacto, descripcion, fecha_entrega, estado, precio)
        )
        conn.commit()
        conn.close()

        flash('Pedido agregado correctamente.')
        return redirect('/pedidos')

    return render_template('agregar.html')

# --- Editar pedido ---
@app.route('/pedidos/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    pedido = conn.execute('SELECT * FROM pedidos WHERE id = ?', (id,)).fetchone()

    if request.method == 'POST':
        cliente = request.form['cliente']
        contacto = request.form['contacto']
        descripcion = request.form['descripcion']
        fecha_entrega = request.form['fecha_entrega']
        estado = request.form['estado']
        precio = request.form['precio']

        conn.execute(
            'UPDATE pedidos SET cliente=?, contacto=?, descripcion=?, fecha_entrega=?, estado=?, precio=? WHERE id=?',
            (cliente, contacto, descripcion, fecha_entrega, estado, precio, id)
        )
        conn.commit()
        conn.close()
        flash('Pedido actualizado correctamente.')
        return redirect('/pedidos')

    conn.close()
    return render_template('editar.html', pedido=pedido)

# --- Eliminar pedido ---
@app.route('/pedidos/eliminar/<int:id>', methods=['GET', 'POST'])
def eliminar(id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    pedido = conn.execute('SELECT * FROM pedidos WHERE id = ?', (id,)).fetchone()

    if pedido is None:
        conn.close()
        flash('Pedido no encontrado.')
        return redirect('/pedidos')

    if request.method == 'POST':
        conn.execute('DELETE FROM pedidos WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        flash('Pedido eliminado correctamente.')
        return redirect('/pedidos')

    conn.close()
    return render_template('eliminar.html', pedido=pedido)



if __name__ == '__main__':
    create_table()
    app.run(debug=True)
