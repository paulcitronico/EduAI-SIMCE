import streamlit as st
import tempfile
from streamlit_pdf_viewer import pdf_viewer

st.set_page_config(page_title="Previsualizador de PDFs", layout="wide")
st.title("Previsualizador de PDFs")

# Subida de archivos
st.write("Sube uno o más archivos PDF")
uploaded_files = st.file_uploader(
    "Elige archivos PDF", type="pdf", accept_multiple_files=True
)

# Guardar archivos temporalmente
if "pdf_files" not in st.session_state:
    st.session_state.pdf_files = {}

for uploaded_file in uploaded_files:
    if uploaded_file.name not in st.session_state.pdf_files:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            st.session_state.pdf_files[uploaded_file.name] = tmp.name

# Control de expansión: solo uno a la vez
if "expanded_pdf" not in st.session_state:
    st.session_state.expanded_pdf = None

# Mostrar vista previa si hay archivos
if st.session_state.pdf_files:
    st.subheader("Vista previa de archivos")
    for name in st.session_state.pdf_files:
        with st.expander(f"📄 {name}", expanded=(st.session_state.expanded_pdf == name)):
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"Ver {name}", key=f"btn_{name}"):
                    st.session_state.expanded_pdf = name
            with col2:
                with open(st.session_state.pdf_files[name], "rb") as f:
                    st.download_button(
                        label="Descargar",
                        data=f,
                        file_name=name,
                        mime="application/pdf",
                        key=f"download_{name}"
                    )

            if st.session_state.expanded_pdf == name:
                pdf_viewer(st.session_state.pdf_files[name], height=600)
else:
    st.info("Sube al menos un archivo PDF para previsualizarlo.")