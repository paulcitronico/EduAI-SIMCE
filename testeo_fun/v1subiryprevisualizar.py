import streamlit as st
import tempfile
from streamlit_pdf_viewer import pdf_viewer

st.set_page_config(page_title="Previsualizador de PDFs", layout="wide")
st.title("Previsualizador de PDFs")

tab1, tab2 = st.tabs(["Subir PDFs", "Vista previa"])

with tab1:
    st.write("Sube uno o más archivos PDF")
    uploaded_files = st.file_uploader(
        "Elige archivos PDF", type="pdf", accept_multiple_files=True
    )

with tab2:
    if not uploaded_files:
        st.warning("Por favor, sube al menos un archivo PDF en la pestaña 'Subir PDFs'.")
    else:
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

        for name in st.session_state.pdf_files:
            with st.expander(f"📄 {name}", expanded=(st.session_state.expanded_pdf == name)):
                if st.button(f"Ver {name}", key=f"btn_{name}"):
                    st.session_state.expanded_pdf = name

                if st.session_state.expanded_pdf == name:
                    pdf_viewer(st.session_state.pdf_files[name], height=600)