import streamlit as st


st.title("EduAI-SIMCE")
st.write("Welcome to the EduAI-SIMCE application!")

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="Mi Plataforma",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- ESTADO ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_section" not in st.session_state:
    st.session_state.current_section = "Unidades"

# ---------------- FUNCIONES ----------------
def login():
    # Aquí iría tu autenticación real
    st.session_state.logged_in = True
    st.rerun()

def logout():
    st.session_state.logged_in = False
    st.session_state.current_section = "Unidades"
    st.rerun()

# ---------------- CSS ----------------
st.markdown(
    """
    <style>
    /* Contenedor de las tabs centrado y con espacio uniforme */
    div[data-baseweb="tab-list"] {
        display: flex !important;
        justify-content: space-evenly !important; /* Espaciado uniforme */
        background-color: #1E3A8A;
        padding: 0.5rem;
        border-radius: 8px;
    }

    /* Estilo base para las pestañas */
    button[role="tab"] {
        color: white !important;
        background-color: transparent !important;
        border-radius: 6px;
        font-weight: bold;
        padding: 0.5rem 1rem;
        transition: background-color 0.3s ease;
    }

    /* Hover */
    button[role="tab"]:hover {
        background-color: rgba(255, 255, 255, 0.2) !important;
    }

    /* Pestaña activa */
    button[role="tab"][aria-selected="true"] {
        background-color: #2563EB !important;
        color: white !important;
        box-shadow: 0px 2px 6px rgba(0,0,0,0.2);
    }
    </style>
    """,
    unsafe_allow_html=True
)
# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.title("Mi Plataforma")

    if st.session_state.logged_in:
        st.write(f"Usuario: **Demo**")
        if st.button("Cerrar sesión", key="logout", use_container_width=True):
            logout()
    else:
        st.subheader("Iniciar sesión")
        usuario = st.text_input("Usuario", key="user")
        clave   = st.text_input("Contraseña", type="password", key="pass")
        if st.button("Entrar", key="login", use_container_width=True):
            # Validación muy sencilla de ejemplo
            if usuario == "admin" and clave == "1234":
                login()
            else:
                st.error("Credenciales incorrectas")

# ---------------- NAVEGACIÓN SUPERIOR ----------------
if st.session_state.logged_in:
    sections = ["Unidades", "Ejercicios", "Revisiones", "Tutoriales", "Lecturas"]
    selected = st.tabs(sections)   # o st.radio, st.selectbox, etc.
    idx = sections.index(st.session_state.current_section)
    with selected[idx]:
        st.session_state.current_section = sections[idx]
        st.header(sections[idx])
        st.write(f"Contenido de **{sections[idx]}** iría aquí.")
else:
    st.info("Por favor, inicia sesión desde el panel lateral.")