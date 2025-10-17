import sqlite3
from database.operations import hash_password

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Tabla de usuarios
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reset_token TEXT,
            reset_token_expiration TEXT
        )
    ''')
    
    # Tabla de archivos
    c.execute('''
        CREATE TABLE IF NOT EXISTS archivos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profesor_id INTEGER NOT NULL,
            nombre_archivo TEXT NOT NULL,
            ruta_archivo TEXT NOT NULL,
            tipo_archivo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            ruta_pdf TEXT,
            fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            seccion_id INTEGER,
            FOREIGN KEY (profesor_id) REFERENCES users(id),
            FOREIGN KEY (seccion_id) REFERENCES secciones(id)
        )
    ''')
    
    # Tabla para tutoriales
    c.execute('''
        CREATE TABLE IF NOT EXISTS tutoriales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profesor_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            descripcion TEXT,
            url_youtube TEXT,
            ruta_video TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profesor_id) REFERENCES users(id)
        )
    ''')
    
    # Tabla de secciones
    c.execute('''
        CREATE TABLE IF NOT EXISTS secciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profesor_id INTEGER NOT NULL,
            nombre TEXT NOT NULL,
            categoria TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profesor_id) REFERENCES users(id)
        )
    ''')
    
    # Verificar y agregar columnas si no existen
    c.execute("PRAGMA table_info(archivos)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'categoria' not in columns:
        c.execute("ALTER TABLE archivos ADD COLUMN categoria TEXT")
    if 'ruta_pdf' not in columns:
        c.execute("ALTER TABLE archivos ADD COLUMN ruta_pdf TEXT")
    if 'seccion_id' not in columns:
        c.execute("ALTER TABLE archivos ADD COLUMN seccion_id INTEGER")
    
    # Verificar columnas de reseteo en users
    c.execute("PRAGMA table_info(users)")
    user_columns = [column[1] for column in c.fetchall()]
    if 'reset_token' not in user_columns:
        c.execute("ALTER TABLE users ADD COLUMN reset_token TEXT")
    if 'reset_token_expiration' not in user_columns:
        c.execute("ALTER TABLE users ADD COLUMN reset_token_expiration TEXT")
    
    # Crear usuario administrador si no existe
    c.execute("SELECT * FROM users WHERE username = 'admin'")
    if not c.fetchone():
        hashed_pw = hash_password('admin123')
        c.execute('''
            INSERT INTO users (username, nombre, apellido, email, password, rol)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', 'Administrador', 'Sistema', 'admin@example.com', hashed_pw, 'admin'))
    
    # Crear profesor por defecto si no existe
    c.execute("SELECT * FROM users WHERE username = 'profesor_default'")
    if not c.fetchone():
        hashed_pw = hash_password('1234')
        c.execute('''
            INSERT INTO users (username, nombre, apellido, email, password, rol)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('profesor_default', 'Profesor', 'Por Defecto', 'profesor_default@system.com', hashed_pw, 'profesor'))
    
    # Tabla para cuestionarios IA
    c.execute('''
        CREATE TABLE IF NOT EXISTS cuestionarios_ia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profesor_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            preguntas TEXT NOT NULL,
            file_info TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profesor_id) REFERENCES users(id)
        )
    ''')

    # Tabla para revisiones de cuestionarios
    c.execute('''
        CREATE TABLE IF NOT EXISTS revisiones_cuestionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            estudiante_id INTEGER NOT NULL,
            cuestionario_id INTEGER NOT NULL,
            titulo_cuestionario TEXT NOT NULL,
            respuestas_usuario TEXT NOT NULL,
            retroalimentacion TEXT NOT NULL,
            puntaje INTEGER NOT NULL,
            total_preguntas INTEGER NOT NULL,
            fecha_realizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (estudiante_id) REFERENCES users(id),
            FOREIGN KEY (cuestionario_id) REFERENCES cuestionarios_ia(id)
        )
    ''')

    conn.commit()
    conn.close()