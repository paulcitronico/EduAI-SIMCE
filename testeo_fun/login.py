import streamlit as st
import sqlite3
import hashlib
import os
from datetime import datetime

# Configuración inicial
st.set_page_config(page_title="Sistema de Login", layout="centered")

# Crear directorio para imágenes si no existe
if not os.path.exists("user_images"):
    os.makedirs("user_images")

# Funciones para la base de datos
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            imagen_path TEXT,
            rol TEXT DEFAULT 'alumno',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crear usuario administrador si no existe
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        hashed_pw = hash_password('admin123')
        c.execute('''
            INSERT INTO users (username, nombre, apellido, email, password, rol)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', 'Administrador', 'Sistema', 'admin@example.com', hashed_pw, 'admin'))
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, nombre, apellido, email, password, imagen_path=None):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        # Todos los nuevos usuarios se registran como 'alumno' por defecto
        c.execute('''
            INSERT INTO users (username, nombre, apellido, email, password, imagen_path, rol)
            VALUES (?, ?, ?, ?, ?, ?, 'alumno')
        ''', (username, nombre, apellido, email, hashed_pw, imagen_path))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    hashed_pw = hash_password(password)
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_pw))
    user = c.fetchone()
    conn.close()
    return user

def update_user_role(user_id, new_role):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("UPDATE users SET rol = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, username, nombre, apellido, email, rol FROM users")
    users = c.fetchall()
    conn.close()
    return users

# Inicializar base de datos
init_db()

# Estado de sesión
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = None
if 'page' not in st.session_state:
    st.session_state.page = "login"
if 'admin_subpage' not in st.session_state:
    st.session_state.admin_subpage = "dashboard"

# Interfaz principal
def login_page():
    st.title("Iniciar Sesión")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Iniciar Sesión")
        
        if submitted:
            user = verify_user(username, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.current_user = user
                st.success(f"Bienvenido {user[2]}!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    
    st.markdown("---")
    if st.button("¿No tienes cuenta? Regístrate"):
        st.session_state.page = "register"
        st.rerun()

def register_page():
    st.title("Crear Nueva Cuenta")
    with st.form("register_form"):
        username = st.text_input("Nombre de usuario")
        nombre = st.text_input("Nombre")
        apellido = st.text_input("Apellido")
        email = st.text_input("E-mail")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirmar Password", type="password")
        imagen = st.file_uploader("Subir una imagen", type=["jpg", "png", "jpeg"])
        
        submitted = st.form_submit_button("Registrarse")
        
        if submitted:
            # Validaciones
            if not all([username, nombre, apellido, email, password]):
                st.error("Por favor completa todos los campos")
            elif password != confirm_password:
                st.error("Las contraseñas no coinciden")
            else:
                # Guardar imagen si se subió
                imagen_path = None
                if imagen:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    imagen_path = f"user_images/{username}_{timestamp}.jpg"
                    with open(imagen_path, "wb") as f:
                        f.write(imagen.getbuffer())
                
                # Agregar usuario a la base de datos (rol 'alumno' por defecto)
                if add_user(username, nombre, apellido, email, password, imagen_path):
                    st.success("¡Cuenta creada exitosamente! Ahora puedes iniciar sesión")
                    st.session_state.page = "login"
                    st.rerun()
                else:
                    st.error("El nombre de usuario o email ya están en uso")
    
    st.markdown("---")
    if st.button("¿Ya tienes cuenta? Inicia sesión"):
        st.session_state.page = "login"
        st.rerun()

def admin_dashboard():
    st.title("Panel de Administración - Dashboard")
    user = st.session_state.current_user
    st.write(f"Bienvenido, {user[2]} {user[3]}")
    st.write(f"Email: {user[4]}")
    st.write(f"Rol: {user[7]}")
    
    if user[6]:
        st.image(user[6], width=200)
    
    st.subheader("Opciones de Administración")
    if st.button("Gestionar Usuarios"):
        st.session_state.admin_subpage = "user_management"
        st.rerun()
    
    if st.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()

def admin_user_management():
    st.title("Gestión de Usuarios")
    
    # Mostrar todos los usuarios
    users = get_all_users()
    st.subheader("Lista de Usuarios")
    
    for user in users:
        user_id, username, nombre, apellido, email, rol = user
        
        # No mostrar al administrador en la lista
        if username == 'admin':
            continue
            
        col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 1])
        with col1:
            st.write(user_id)
        with col2:
            st.write(username)
        with col3:
            st.write(f"{nombre} {apellido}")
        with col4:
            st.write(email)
        with col5:
            # Selector de rol solo para el administrador
            new_rol = st.selectbox(
                "Rol",
                ['alumno', 'profesor'],
                index=0 if rol == 'alumno' else 1,
                key=f"rol_{user_id}"
            )
            
            if new_rol != rol:
                update_user_role(user_id, new_rol)
                st.success(f"Rol de {username} actualizado a {new_rol}")
                st.rerun()
    
    if st.button("Volver al Dashboard"):
        st.session_state.admin_subpage = "dashboard"
        st.rerun()

def profesor_page():
    user = st.session_state.current_user
    st.title(f"Panel del Profesor - {user[2]} {user[3]}")
    st.write(f"Email: {user[4]}")
    st.write(f"Rol: {user[7]}")
    
    if user[6]:
        st.image(user[6], width=200)
    
    st.subheader("Funcionalidades para Profesores")
    st.write("Aquí puedes agregar contenido específico para profesores:")
    st.write("- Gestión de cursos")
    st.write("- Creación de exámenes")
    st.write("- Seguimiento de estudiantes")
    
    if st.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()

def alumno_page():
    user = st.session_state.current_user
    st.title(f"Panel del Alumno - {user[2]} {user[3]}")
    st.write(f"Email: {user[4]}")
    st.write(f"Rol: {user[7]}")
    
    if user[6]:
        st.image(user[6], width=200)
    
    st.subheader("Funcionalidades para Alumnos")
    st.write("Aquí puedes agregar contenido específico para alumnos:")
    st.write("- Ver tus cursos")
    st.write("- Realizar exámenes")
    st.write("- Consultar calificaciones")
    
    if st.button("Cerrar Sesión"):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.rerun()

def main_page():
    user = st.session_state.current_user
    rol = user[7]
    
    # Redirigir según el rol
    if rol == 'admin':
        if st.session_state.admin_subpage == "dashboard":
            admin_dashboard()
        elif st.session_state.admin_subpage == "user_management":
            admin_user_management()
    elif rol == 'profesor':
        profesor_page()
    else:  # alumno
        alumno_page()

# Navegación entre páginas
if st.session_state.logged_in:
    main_page()
else:
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "register":
        register_page()