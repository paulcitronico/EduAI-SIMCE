import streamlit as st
from database.models import init_db
from auth.authentication import login_page, register_page, reset_password_page, reset_password_confirm_page
from roles.admin import admin_dashboard, admin_user_management
from roles.profesor import profesor_page
from roles.alumno import alumno_page
import config

# Configuración inicial
st.set_page_config(page_title=config.PAGE_TITLE, layout=config.PAGE_LAYOUT)

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
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = "Unidades"
if 'reset_token' not in st.session_state:
    st.session_state.reset_token = None
if 'password_reset_success' not in st.session_state:
    st.session_state.password_reset_success = False
if 'expanded_pdf' not in st.session_state:
    st.session_state.expanded_pdf = None

# Verificar si hay un token de restablecimiento en la URL
query_params = st.query_params
if 'reset_token' in query_params and not st.session_state.logged_in and not st.session_state.password_reset_success:
    st.session_state.reset_token = query_params['reset_token']
    st.session_state.page = "reset_password_confirm"

def main_page():
    user = st.session_state.current_user
    rol = user[7]
    
    if rol == 'admin':
        if st.session_state.admin_subpage == "dashboard":
            admin_dashboard()
        elif st.session_state.admin_subpage == "user_management":
            admin_user_management()
    elif rol == 'profesor':
        profesor_page()
    else:
        alumno_page()

# Navegación entre páginas
if st.session_state.logged_in:
    main_page()
else:
    if st.session_state.page == "login":
        login_page()
    elif st.session_state.page == "register":
        register_page()
    elif st.session_state.page == "reset_password":
        reset_password_page()
    elif st.session_state.page == "reset_password_confirm":
        reset_password_confirm_page()