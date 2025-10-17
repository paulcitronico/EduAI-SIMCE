import sqlite3
import hashlib
import os
from datetime import datetime
import streamlit as st
from auth.email_service import send_email

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, nombre, apellido, email, password, imagen_path=None):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        hashed_pw = hash_password(password)
        c.execute('''
            INSERT INTO users (username, nombre, apellido, email, password, imagen_path, rol)
            VALUES (?, ?, ?, ?, ?, ?, 'alumno')
        ''', (username, nombre, apellido, email, hashed_pw, imagen_path))
        conn.commit()
        
        # Enviar correo de bienvenida
        subject = "Bienvenido al Sistema"
        body = f"""
        Hola {nombre},
        
        Te damos la bienvenida a nuestro sistema educativo.
        
        Tu cuenta ha sido creada exitosamente con los siguientes datos:
        - Usuario: {username}
        - Nombre: {nombre} {apellido}
        - Correo: {email}
        
        Para iniciar sesión, visita nuestra aplicación e ingresa tus credenciales.
        
        Si tienes alguna pregunta, no dudes en contactarnos.
        
        Saludos,
        El equipo del sistema
        """
        
        if send_email(email, subject, body):
            st.success("¡Cuenta creada exitosamente! Revisa tu correo para el mensaje de bienvenida.")
        else:
            st.warning("Tu cuenta fue creada, pero hubo un error al enviar el correo de bienvenida.")
        
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

def delete_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Obtener el ID del profesor por defecto
    c.execute("SELECT id FROM users WHERE username = 'profesor_default'")
    default_teacher = c.fetchone()
    
    if not default_teacher:
        conn.close()
        return False, "No se encontró el profesor por defecto en el sistema"
    
    default_teacher_id = default_teacher[0]
    
    # Verificar que no se intente eliminar al profesor por defecto
    if user_id == default_teacher_id:
        conn.close()
        return False, "No se puede eliminar al profesor por defecto del sistema"
    
    c.execute("SELECT imagen_path, rol FROM users WHERE id = ?", (user_id,))
    result = c.fetchone()
    
    if result:
        imagen_path, rol = result
        
        try:
            if imagen_path and os.path.exists(imagen_path):
                os.remove(imagen_path)
        except Exception as e:
            conn.close()
            return False, f"Error al eliminar la imagen: {str(e)}"
        
        try:
            if rol == 'profesor':
                # Reasignar todos los recursos al profesor por defecto
                c.execute("UPDATE archivos SET profesor_id = ? WHERE profesor_id = ?", 
                         (default_teacher_id, user_id))
                c.execute("UPDATE tutoriales SET profesor_id = ? WHERE profesor_id = ?", 
                         (default_teacher_id, user_id))
                c.execute("UPDATE secciones SET profesor_id = ? WHERE profesor_id = ?", 
                         (default_teacher_id, user_id))
            
            # Eliminar el usuario
            c.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
            return True, "Usuario eliminado exitosamente"
            
        except sqlite3.IntegrityError as e:
            conn.close()
            return False, f"Error de integridad de base de datos: {str(e)}"
        except Exception as e:
            conn.close()
            return False, f"Error inesperado: {str(e)}"
    else:
        conn.close()
        return False, "Usuario no encontrado en la base de datos"

# Funciones para archivos
def guardar_archivo(profesor_id, archivo, categoria, seccion_id=None):
    from utils.file_processing import convertir_pptx_a_pdf
    import config
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"{timestamp}_{archivo.name}"
    ruta_archivo = f"{config.ARCHIVOS_PROFESORES_DIR}/{nombre_archivo}"
    
    with open(ruta_archivo, "wb") as f:
        f.write(archivo.getbuffer())
    
    ruta_pdf = None
    
    if archivo.type in ['application/vnd.openxmlformats-officedocument.presentationml.presentation',
                       'application/vnd.ms-powerpoint',
                       'application/vnd.ms-powerpoint.presentation.macroEnabled.12']:
        try:
            nombre_pdf = f"{timestamp}_{os.path.splitext(archivo.name)[0]}.pdf"
            ruta_pdf = f"{config.ARCHIVOS_PROFESORES_DIR}/{nombre_pdf}"
            
            if convertir_pptx_a_pdf(ruta_archivo, ruta_pdf):
                print(f"Archivo convertido a PDF: {nombre_pdf}")
            else:
                ruta_pdf = None
                print("No se pudo convertir el archivo a PDF")
        except Exception as e:
            ruta_pdf = None
            print(f"Error al convertir el archivo a PDF: {str(e)}")
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO archivos (profesor_id, nombre_archivo, ruta_archivo, tipo_archivo, categoria, ruta_pdf, seccion_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (profesor_id, archivo.name, ruta_archivo, archivo.type, categoria, ruta_pdf, seccion_id))
    conn.commit()
    conn.close()
    
    return ruta_archivo

def obtener_archivos(categoria=None, profesor_id=None, seccion_id=None):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    query = '''
        SELECT a.id, a.nombre_archivo, a.ruta_archivo, a.tipo_archivo, a.fecha_subida, 
               COALESCE(u.nombre, 'Profesor eliminado'), COALESCE(u.apellido, ''), 
               a.categoria, a.ruta_pdf, a.seccion_id
        FROM archivos a
        LEFT JOIN users u ON a.profesor_id = u.id
    '''
    
    params = []
    conditions = []
    
    if categoria:
        conditions.append("a.categoria = ?")
        params.append(categoria)
    
    if profesor_id:
        conditions.append("a.profesor_id = ?")
        params.append(profesor_id)
    
    if seccion_id:
        conditions.append("a.seccion_id = ?")
        params.append(seccion_id)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY a.fecha_subida DESC"
    
    c.execute(query, params)
    archivos = c.fetchall()
    conn.close()
    return archivos

def eliminar_archivo(archivo_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute("SELECT ruta_archivo, ruta_pdf FROM archivos WHERE id = ?", (archivo_id,))
    resultado = c.fetchone()
    
    if resultado:
        ruta_archivo, ruta_pdf = resultado
        
        try:
            if os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)
            
            if ruta_pdf and os.path.exists(ruta_pdf):
                os.remove(ruta_pdf)
        except Exception as e:
            conn.close()
            return False, f"Error al eliminar archivos físicos: {str(e)}"
        
        c.execute("DELETE FROM archivos WHERE id = ?", (archivo_id,))
        conn.commit()
        conn.close()
        return True, "Archivo eliminado exitosamente"
    else:
        conn.close()
        return False, "Archivo no encontrado en la base de datos"

# Funciones para tutoriales
def agregar_tutorial(profesor_id, titulo, descripcion, url_youtube=None, ruta_video=None):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO tutoriales (profesor_id, titulo, descripcion, url_youtube, ruta_video)
            VALUES (?, ?, ?, ?, ?)
        ''', (profesor_id, titulo, descripcion, url_youtube, ruta_video))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al agregar tutorial: {str(e)}")
        return False
    finally:
        conn.close()

def obtener_tutoriales():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''
        SELECT t.id, t.titulo, t.descripcion, t.url_youtube, t.ruta_video, t.fecha_creacion, u.nombre, u.apellido
        FROM tutoriales t
        JOIN users u ON t.profesor_id = u.id
        ORDER BY t.fecha_creacion DESC
    ''')
    tutoriales = c.fetchall()
    conn.close()
    return tutoriales

def eliminar_tutorial(tutorial_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute("SELECT ruta_video FROM tutoriales WHERE id = ?", (tutorial_id,))
    resultado = c.fetchone()
    
    if resultado:
        ruta_video = resultado[0]
        
        try:
            if ruta_video and os.path.exists(ruta_video):
                os.remove(ruta_video)
        except Exception as e:
            conn.close()
            return False, f"Error al eliminar archivo de video: {str(e)}"
        
        c.execute("DELETE FROM tutoriales WHERE id = ?", (tutorial_id,))
        conn.commit()
        conn.close()
        return True, "Tutorial eliminado exitosamente"
    else:
        conn.close()
        return False, "Tutorial no encontrado en la base de datos"

# Funciones para secciones
def crear_seccion(profesor_id, nombre, categoria):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO secciones (profesor_id, nombre, categoria)
            VALUES (?, ?, ?)
        ''', (profesor_id, nombre, categoria))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al crear sección: {str(e)}")
        return False
    finally:
        conn.close()

def obtener_secciones(categoria=None, profesor_id=None):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        query = '''
            SELECT s.id, s.nombre, s.created_at, u.nombre, u.apellido
            FROM secciones s
            LEFT JOIN users u ON s.profesor_id = u.id
        '''
        
        params = []
        conditions = []
        
        if categoria:
            conditions.append("s.categoria = ?")
            params.append(categoria)
        
        if profesor_id:
            conditions.append("s.profesor_id = ?")
            params.append(profesor_id)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY s.created_at"
        
        c.execute(query, params)
        secciones = c.fetchall()
        return secciones
    except Exception as e:
        print(f"Error al obtener secciones: {str(e)}")
        return []
    finally:
        conn.close()

def eliminar_seccion(seccion_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("SELECT COUNT(*) FROM archivos WHERE seccion_id = ?", (seccion_id,))
        count = c.fetchone()[0]
        
        if count > 0:
            c.execute("UPDATE archivos SET seccion_id = NULL WHERE seccion_id = ?", (seccion_id,))
        
        c.execute("DELETE FROM secciones WHERE id = ?", (seccion_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al eliminar sección: {str(e)}")
        return False
    finally:
        conn.close()

def mover_archivo_seccion(archivo_id, nueva_seccion_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    try:
        c.execute("UPDATE archivos SET seccion_id = ? WHERE id = ?", (nueva_seccion_id, archivo_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error al mover archivo: {str(e)}")
        return False
    finally:
        conn.close()

def listar_estudiantes_inscritos():
    st.title("Lista de Alumnos Inscritos")
    
    # Obtener todos los usuarios con rol 'alumno'
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, username, nombre, apellido, email FROM users WHERE rol = 'alumno'")
    estudiantes = c.fetchall()
    conn.close()
    
    if not estudiantes:
        st.info("No hay alumnos inscritos.")
    else:
        # Mostrar tabla con los datos
        st.subheader("Alumnos Registrados")
        
        # Preparar datos para la tabla
        datos_estudiantes = []
        for est in estudiantes:
            datos_estudiantes.append({
                "ID": est[0],
                "Usuario": est[1],
                "Nombre": est[2],
                "Apellido": est[3],
                "Correo": est[4]
            })
        
        # Mostrar la tabla
        st.dataframe(datos_estudiantes)
        
        # Botón para descargar en CSV
        if st.button("Descargar listado"):
            # Crear un archivo CSV en memoria
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            # Escribir encabezados
            writer.writerow(["ID", "Usuario", "Nombre", "Apellido", "Correo"])
            
            # Escribir datos
            for est in estudiantes:
                writer.writerow(est)
            
            # Preparar para descarga
            csv_data = output.getvalue().encode('utf-8')
            
            st.download_button(
                label="Descargar CSV",
                data=csv_data,
                file_name="listado_alumnos.csv",
                mime="text/csv"
            )

