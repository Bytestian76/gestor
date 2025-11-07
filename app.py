from flask import Flask, render_template, request, redirect, session, flash, url_for
from flask_dance.contrib.google import make_google_blueprint, google
import sqlite3
from itsdangerous import URLSafeTimedSerializer as Serializer

app = Flask(__name__)
app.secret_key = 'lunenauditore'

# --- Conexión a la base de datos ---
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

serializer = Serializer(app.secret_key, salt='password-reset-salt')

# --- Configuración de Google OAuth ---
google_bp = make_google_blueprint(
    client_id='882145391019-suqnreqe7vjdgjjkc7hnsk0futsi4j3l.apps.googleusercontent.com',
    client_secret='tu_client_secret',
    redirect_to='google_login_callback',  # Nombre del callback
    scope=["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email"]
)

app.register_blueprint(google_bp, url_prefix="/google_login")

# --- Ruta para iniciar sesión con Google ---
@app.route('/login_google')
def login_google():
    return redirect(url_for('google.login'))

# --- Callback de Google (Después de la autenticación) ---
@app.route('/google_login/callback')
def google_login_callback():
    if not google.authorized:
        flash("No se pudo iniciar sesión con Google. Inténtalo nuevamente.")
        return redirect(url_for('login'))

    # Obtener la información del usuario
    user_info = google.get('/plus/v1/people/me')
    user_data = user_info.json()

    email = user_data['emails'][0]['value']
    nombre = user_data['displayName']

    # Verificar si el usuario ya está registrado en tu base de datos
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
    conn.close()

    if user:
        # Si el usuario existe, iniciar sesión
        session['user_id'] = user['id']
        session['user_email'] = user['email']
        session['user_nombre'] = user['nombre']
        flash('Bienvenido nuevamente, ' + user['nombre'] + '!')
        return redirect(url_for('index'))
    else:
        # Si el usuario no está registrado, agregarlo
        conn = get_db_connection()
        conn.execute('INSERT INTO usuarios (nombre, email, password) VALUES (?, ?, ?)', (nombre, email, 'google_login'))
        conn.commit()
        conn.close()
        flash('Usuario creado con éxito, has iniciado sesión con Google.')
        return redirect(url_for('index'))

# --- Log out ---
@app.route('/logout')
def logout():
    session.clear()
    flash('Sesión cerrada correctamente.')
    return redirect('/login')

# --- Página principal (Index) ---
@app.route("/")
def home():
    return render_template("index.html")
    
@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect('/login')

    nombre = session.get('user_nombre', 'Usuario')
    return render_template('index.html', nombre=nombre)

# --- Rutas adicionales para tu aplicación ---
# Las demás rutas permanecen igual que en tu código original.

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Render asigna el puerto aquí
    app.run(host="0.0.0.0", port=port, debug=True)  # host y puerto correctos






