import streamlit as st
from database.operations import add_user, verify_user
from auth.email_service import send_email
import os
from datetime import datetime
from utils.common import go_to_login

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
                st.session_state.expanded_pdf = None
                st.success(f"Bienvenido {user[2]}!")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("¿No tienes cuenta? Regístrate"):
            st.session_state.page = "register"
            st.rerun()
    with col2:
        if st.button("¿Olvidaste tu contraseña?"):
            st.session_state.page = "reset_password"
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
            if not all([username, nombre, apellido, email, password]):
                st.error("Por favor completa todos los campos")
            elif password != confirm_password:
                st.error("Las contraseñas no coinciden")
            else:
                imagen_path = None
                if imagen:
                    import config
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    imagen_path = f"{config.USER_IMAGES_DIR}/{username}_{timestamp}.jpg"
                    with open(imagen_path, "wb") as f:
                        f.write(imagen.getbuffer())
                
                if add_user(username, nombre, apellido, email, password, imagen_path):
                    go_to_login()
                else:
                    st.error("El nombre de usuario o email ya están en uso")
    
    st.markdown("---")
    if st.button("¿Ya tienes cuenta? Inicia sesión"):
        go_to_login()

def reset_password_page():
    st.title("Restablecer Contraseña")
    st.write("Ingresa tu correo electrónico y te enviaremos un enlace para restablecer tu contraseña.")
    
    from auth.email_service import show_all_emails
    if st.button("Mostrar todos los correos (depuración)"):
        all_emails = show_all_emails()
        st.write("Correos registrados:")
        for email in all_emails:
            st.write(f"- {email}")
    
    with st.form("reset_password_form"):
        email = st.text_input("Correo electrónico")
        submitted = st.form_submit_button("Enviar Enlace")
        
        if submitted:
            from auth.password_reset import generate_reset_token
            
            import sqlite3
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute("SELECT email FROM users WHERE LOWER(email) = LOWER(?)", (email,))
            user_email = c.fetchone()
            conn.close()
            
            if user_email:
                st.info(f"Correo encontrado: {user_email[0]}")
            else:
                st.warning("Correo no encontrado en la base de datos.")
            
            success, message = generate_reset_token(email)
            if success:
                st.success(message)
                go_to_login()
            else:
                st.error(message)
    st.markdown("---")
    if st.button("¿Ya tienes cuenta? Inicia sesión"):
        go_to_login()

def reset_password_confirm_page():
    st.title("Restablecer Contraseña")
    token = st.session_state.reset_token
    
    if st.session_state.password_reset_success:
        st.success("¡Contraseña restablecida exitosamente!")
        st.write("Ya puedes iniciar sesión con tu nueva contraseña.")
        
        if st.button("¿Ya tienes cuenta? Inicia sesión"):
            st.session_state.password_reset_success = False
            go_to_login()
        return
    
    with st.form("reset_password_confirm_form"):
        new_password = st.text_input("Nueva Contraseña", type="password")
        confirm_password = st.text_input("Confirmar Nueva Contraseña", type="password")
        submitted = st.form_submit_button("Restablecer Contraseña")
        
        if submitted:
            from auth.password_reset import reset_password_with_token
            
            if new_password != confirm_password:
                st.error("Las contraseñas no coinciden.")
            else:
                success, message = reset_password_with_token(token, new_password)
                if success:
                    st.session_state.password_reset_success = True
                    st.rerun()
                else:
                    st.error(message)
    
    st.markdown("---")
    if st.button("¿Ya tienes cuenta? Inicia sesión"):
        go_to_login()