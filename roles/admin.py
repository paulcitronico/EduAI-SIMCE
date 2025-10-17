import streamlit as st
from database.operations import get_all_users, update_user_role, delete_user
from database.operations import obtener_archivos, eliminar_archivo
from utils.common import logout

def admin_dashboard():
    st.title("Panel de Administración - Dashboard")
    user = st.session_state.current_user
    st.write(f"Bienvenido, {user[2]} {user[3]}")
    st.write(f"Email: {user[4]}")
    st.write(f"Rol: {user[7]}")
    
    if user[6]:
        st.image(user[6], width=200)
    
    st.subheader("Opciones de Administración")
    if st.button("Gestionar Usuarios", key="manage_users"):
        st.session_state.admin_subpage = "user_management"
        st.rerun()
    
    if st.button("Cerrar Sesión", key="logout_admin"):
        logout()

def admin_user_management():
    st.title("Gestión de Usuarios")
    
    users = get_all_users()
    st.subheader("Lista de Usuarios")
    
    for user in users:
        user_id, username, nombre, apellido, email, rol = user
        
        if username == 'admin':
            continue
            
        col1, col2, col3, col4, col5, col6 = st.columns([1, 2, 2, 2, 2, 1])
        with col1:
            st.write(user_id)
        with col2:
            st.write(username)
        with col3:
            st.write(f"{nombre} {apellido}")
        with col4:
            st.write(email)
        with col5:
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
        with col6:
            if st.button("🗑️", key=f"delete_{user_id}"):
                success, message = delete_user(user_id)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    if st.button("Volver al Dashboard", key="back_to_dashboard"):
        st.session_state.admin_subpage = "dashboard"
        st.rerun()

def listar_estudiantes_inscritos():
    st.title("Lista de Alumnos Inscritos")
    
    import sqlite3
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT id, username, nombre, apellido, email FROM users WHERE rol = 'alumno'")
    estudiantes = c.fetchall()
    conn.close()
    
    if not estudiantes:
        st.info("No hay alumnos inscritos.")
    else:
        st.subheader("Alumnos Registrados")
        
        datos_estudiantes = []
        for est in estudiantes:
            datos_estudiantes.append({
                "ID": est[0],
                "Usuario": est[1],
                "Nombre": est[2],
                "Apellido": est[3],
                "Correo": est[4]
            })
        
        st.dataframe(datos_estudiantes)
        
        if st.button("Descargar listado", key="download_listado"):
            import csv
            from io import StringIO
            
            output = StringIO()
            writer = csv.writer(output)
            
            writer.writerow(["ID", "Usuario", "Nombre", "Apellido", "Correo"])
            
            for est in estudiantes:
                writer.writerow(est)
            
            csv_data = output.getvalue().encode('utf-8')
            
            st.download_button(
                label="Descargar CSV",
                data=csv_data,
                file_name="listado_alumnos.csv",
                mime="text/csv"
            )
