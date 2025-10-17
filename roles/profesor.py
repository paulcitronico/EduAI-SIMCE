import streamlit as st
import os
from database.operations import obtener_archivos, guardar_archivo, eliminar_archivo
from database.operations import crear_seccion, obtener_secciones, eliminar_seccion, mover_archivo_seccion
from database.operations import agregar_tutorial, obtener_tutoriales, eliminar_tutorial
from utils.preview_utils import mostrar_vista_previa
from utils.file_processing import extraer_id_youtube
from database.operations import listar_estudiantes_inscritos
from utils.common import logout

def profesor_sidebar():
    user = st.session_state.current_user
    st.sidebar.image(user[6] if user[6] else "https://via.placeholder.com/150", width=150)
    st.sidebar.write(f"**{user[2]} {user[3]}**")
    st.sidebar.write(f"Rol: {user[7]}")
    
    st.sidebar.markdown("---")
        
    if st.sidebar.button("Cerrar Sesión"):
        logout()

def mostrar_unidades_con_secciones():
    user = st.session_state.current_user
    profesor_id = user[0]
    categoria = "Unidades"
    
    st.title(f"Gestión de {categoria}")
    
    secciones = obtener_secciones(categoria=categoria)
    
    with st.expander("Crear Nueva Sección", expanded=False):
        with st.form("form_nueva_seccion"):
            nombre_seccion = st.text_input("Nombre de la Sección")
            submitted = st.form_submit_button("Crear Sección")
            
            if submitted:
                if nombre_seccion:
                    if crear_seccion(profesor_id, nombre_seccion, categoria):
                        st.success(f"Sección '{nombre_seccion}' creada exitosamente")
                        st.rerun()
                    else:
                        st.error("Error al crear la sección")
                else:
                    st.error("El nombre de la sección es obligatorio")
    
    if not secciones:
        st.info("No hay secciones creadas. Crea una nueva sección para empezar.")
    else:
        todos_los_archivos = obtener_archivos(categoria=categoria)
        
        archivos_por_seccion = {}
        archivos_sin_seccion = []
        
        for archivo in todos_los_archivos:
            arch_id, nombre_archivo, ruta_archivo, tipo_archivo, fecha_subida, nombre_profesor, apellido_profesor, categoria_archivo, ruta_pdf, seccion_id = archivo
            
            if seccion_id:
                if seccion_id not in archivos_por_seccion:
                    archivos_por_seccion[seccion_id] = []
                archivos_por_seccion[seccion_id].append(archivo)
            else:
                archivos_sin_seccion.append(archivo)
        
        for seccion in secciones:
            seccion_id, nombre_seccion, created_at, nombre_profesor_seccion, apellido_profesor_seccion = seccion
            
            with st.container():
                st.markdown(f"### {nombre_seccion}")
                st.write(f"Creada por: {nombre_profesor_seccion} {apellido_profesor_seccion} - {created_at}")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    with st.form(f"form_subir_{seccion_id}"):
                        uploaded_files = st.file_uploader(
                            f"Subir archivos a {nombre_seccion}", 
                            type=["pdf", "docx", "pptx", "jpg", "png", "jpeg"], 
                            accept_multiple_files=True,
                            key=f"uploader_{seccion_id}"
                        )
                        submitted = st.form_submit_button("Subir Archivos")
                        
                        if submitted and uploaded_files:
                            for uploaded_file in uploaded_files:
                                guardar_archivo(profesor_id, uploaded_file, categoria, seccion_id)
                            st.success(f"Se han subido {len(uploaded_files)} archivos a {nombre_seccion}")
                            st.rerun()
                
                with col2:
                    if seccion[0] == profesor_id:
                        if st.button(f"Eliminar Sección", key=f"eliminar_seccion_{seccion_id}"):
                            if eliminar_seccion(seccion_id):
                                st.success(f"Sección '{nombre_seccion}' eliminada exitosamente")
                                st.rerun()
                            else:
                                st.error("Error al eliminar la sección")
                
                if seccion_id in archivos_por_seccion and archivos_por_seccion[seccion_id]:
                    st.subheader(f"Archivos en {nombre_seccion}")
                    
                    for archivo in archivos_por_seccion[seccion_id]:
                        arch_id, nombre_archivo, ruta_archivo, tipo_archivo, fecha_subida, nombre_profesor, apellido_profesor, categoria_archivo, ruta_pdf, archivo_seccion_id = archivo
                        
                        with st.expander(f"{nombre_archivo} - {fecha_subida} (Subido por: {nombre_profesor} {apellido_profesor})"):
                            st.write(f"Tipo: {tipo_archivo}")
                            
                            if tipo_archivo == 'application/pdf':
                                col1, col2 = st.columns([1, 1])
                                with col1:
                                    if st.button(f"Ver {nombre_archivo}", key=f"btn_{arch_id}"):
                                        st.session_state.expanded_pdf = nombre_archivo
                                with col2:
                                    with open(ruta_archivo, "rb") as f:
                                        st.download_button(
                                            label="Descargar",
                                            data=f,
                                            file_name=nombre_archivo,
                                            mime="application/pdf",
                                            key=f"download_{arch_id}"
                                        )
                                
                                if 'expanded_pdf' in st.session_state and st.session_state.expanded_pdf == nombre_archivo:
                                    try:
                                        from streamlit_pdf_viewer import pdf_viewer
                                        pdf_viewer(ruta_archivo, height=600)
                                    except Exception as e:
                                        st.error(f"No se pudo mostrar el PDF: {str(e)}")
                            else:
                                mostrar_vista_previa(ruta_archivo, tipo_archivo, ruta_pdf)
                            
                            st.subheader("Mover a otra sección")
                            opciones_secciones = [("Sin sección", None)] + [(s[1], s[0]) for s in secciones if s[0] != seccion_id]
                            seccion_destino = st.selectbox(
                                "Seleccionar sección de destino",
                                options=[opcion[0] for opcion in opciones_secciones],
                                key=f"mover_{arch_id}"
                            )
                            
                            seccion_destino_id = next((opcion[1] for opcion in opciones_secciones if opcion[0] == seccion_destino), None)
                            
                            if st.button("Mover Archivo", key=f"btn_mover_{arch_id}"):
                                if mover_archivo_seccion(arch_id, seccion_destino_id):
                                    st.success(f"Archivo movido a {seccion_destino}")
                                    st.rerun()
                                else:
                                    st.error("Error al mover el archivo")
                            
                            if st.button("Eliminar Archivo", key=f"eliminar_archivo_{arch_id}"):
                                if eliminar_archivo(arch_id):
                                    st.success("Archivo eliminado exitosamente")
                                    st.rerun()
                                else:
                                    st.error("Error al eliminar el archivo")
                else:
                    st.info(f"No hay archivos en {nombre_seccion}")
                
                st.markdown("---")
        
        if archivos_sin_seccion:
            st.subheader("Archivos sin Sección")
            
            for archivo in archivos_sin_seccion:
                arch_id, nombre_archivo, ruta_archivo, tipo_archivo, fecha_subida, nombre_profesor, apellido_profesor, categoria_archivo, ruta_pdf, seccion_id = archivo
                
                with st.expander(f"{nombre_archivo} - {fecha_subida} (Subido por: {nombre_profesor} {apellido_profesor})"):
                    st.write(f"Tipo: {tipo_archivo}")
                    
                    if tipo_archivo == 'application/pdf':
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button(f"Ver {nombre_archivo}", key=f"btn_{arch_id}"):
                                st.session_state.expanded_pdf = nombre_archivo
                        with col2:
                            with open(ruta_archivo, "rb") as f:
                                st.download_button(
                                    label="Descargar",
                                    data=f,
                                    file_name=nombre_archivo,
                                    mime="application/pdf",
                                    key=f"download_{arch_id}"
                                )
                        
                        if 'expanded_pdf' in st.session_state and st.session_state.expanded_pdf == nombre_archivo:
                            try:
                                from streamlit_pdf_viewer import pdf_viewer
                                pdf_viewer(ruta_archivo, height=600)
                            except Exception as e:
                                st.error(f"No se pudo mostrar el PDF: {str(e)}")
                    else:
                        mostrar_vista_previa(ruta_archivo, tipo_archivo, ruta_pdf)
                    
                    st.subheader("Mover a una sección")
                    opciones_secciones = [("Sin sección", None)] + [(s[1], s[0]) for s in secciones]
                    seccion_destino = st.selectbox(
                        "Seleccionar sección de destino",
                        options=[opcion[0] for opcion in opciones_secciones],
                        key=f"mover_{arch_id}"
                    )
                    
                    seccion_destino_id = next((opcion[1] for opcion in opciones_secciones if opcion[0] == seccion_destino), None)
                    
                    if st.button("Mover Archivo", key=f"btn_mover_{arch_id}"):
                        if mover_archivo_seccion(arch_id, seccion_destino_id):
                            st.success(f"Archivo movido a {seccion_destino}")
                            st.rerun()
                        else:
                            st.error("Error al mover el archivo")
                    
                    if st.button("Eliminar Archivo", key=f"eliminar_archivo_{arch_id}"):
                        if eliminar_archivo(arch_id):
                            st.success("Archivo eliminado exitosamente")
                            st.rerun()
                        else:
                            st.error("Error al eliminar el archivo")


def mostrar_revisiones():
    st.title("Revisiones de Estudiantes")
    
    # Obtener todas las revisiones de los estudiantes
    import sqlite3
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT r.id, r.titulo_cuestionario, r.puntaje, r.total_preguntas, 
               r.fecha_realizacion, u.nombre, u.apellido, u.username
        FROM revisiones_cuestionarios r
        JOIN users u ON r.estudiante_id = u.id
        ORDER BY r.fecha_realizacion DESC
    ''')
    
    revisiones = c.fetchall()
    conn.close()
    
    if not revisiones:
        st.info("Los estudiantes aún no han completado cuestionarios.")
        return
    
    # Mostrar estadísticas generales
    total_revisiones = len(revisiones)
    promedio_puntaje = sum(rev[2]/rev[3]*100 for rev in revisiones) / total_revisiones
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de Revisiones", total_revisiones)
    with col2:
        st.metric("Promedio General", f"{promedio_puntaje:.1f}%")
    
    st.markdown("---")
    
    # Mostrar tabla de revisiones
    st.subheader("Historial de Revisiones")
    
    datos_revisiones = []
    for rev in revisiones:
        rev_id, titulo, puntaje, total, fecha, nombre, apellido, username = rev
        porcentaje = (puntaje / total) * 100
        datos_revisiones.append({
            "Estudiante": f"{nombre} {apellido} ({username})",
            "Cuestionario": titulo,
            "Puntaje": f"{puntaje}/{total}",
            "Porcentaje": f"{porcentaje:.1f}%",
            "Fecha": fecha
        })
    
    st.dataframe(datos_revisiones, use_container_width=True)
    
    # Opción para descargar reporte
    if st.button("📊 Generar Reporte de Revisiones"):
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow(["Estudiante", "Cuestionario", "Puntaje", "Porcentaje", "Fecha"])
        
        for rev in revisiones:
            rev_id, titulo, puntaje, total, fecha, nombre, apellido, username = rev
            porcentaje = (puntaje / total) * 100
            writer.writerow([
                f"{nombre} {apellido} ({username})",
                titulo,
                f"{puntaje}/{total}",
                f"{porcentaje:.1f}%",
                fecha
            ])
        
        csv_data = output.getvalue().encode('utf-8')
        
        st.download_button(
            label="📥 Descargar Reporte CSV",
            data=csv_data,
            file_name="reporte_revisiones.csv",
            mime="text/csv"
        )

def profesor_page():
    user = st.session_state.current_user
    
    profesor_sidebar()
    
    st.title(f"Bienvenido, {user[2]} {user[3]}")
    
    st.subheader("Navegación")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("Unidades", key="main_unidades"):
            st.session_state.selected_category = "Unidades"
            st.rerun()
    with col2:
        if st.button("Cuestionarios IA", key="main_cuestionarios"):
            st.session_state.selected_category = "Cuestionarios IA"
            st.rerun()
    with col3:
        if st.button("Revisiones", key="main_revisiones"):
            st.session_state.selected_category = "Revisiones"
            st.rerun()
    with col4:
        if st.button("Tutoriales", key="main_tutoriales"):
            st.session_state.selected_category = "Tutoriales"
            st.rerun()
    with col5:
        if st.button("Guías", key="main_guias"):
            st.session_state.selected_category = "Guías"
            st.rerun()
    with col6:
        if st.button("Lista de Alumnos", key="main_lista_alumnos"):
            st.session_state.selected_category = "Lista de Alumnos"
            st.rerun()
    
    category = st.session_state.selected_category
    
    if category == "Lista de Alumnos":
        listar_estudiantes_inscritos()
    elif category == "Cuestionarios IA":
        mostrar_cuestionarios_ia()
    elif category == "Tutoriales":
        st.title("Gestión de Tutoriales")
        
        with st.form("form_tutorial"):
            st.subheader("Agregar Nuevo Tutorial")
            titulo = st.text_input("Título del tutorial")
            descripcion = st.text_area("Descripción")
            
            col1, col2 = st.columns(2)
            with col1:
                url_youtube = st.text_input("URL de YouTube (opcional)", placeholder="https://www.youtube.com/watch?v=...")
            with col2:
                video_file = st.file_uploader("O subir video MP4 (opcional)", type=["mp4"])
            
            submitted = st.form_submit_button("Agregar Tutorial")
            
            if submitted:
                if not titulo:
                    st.error("El título es obligatorio")
                elif not url_youtube and not video_file:
                    st.error("Debes proporcionar una URL de YouTube o subir un video MP4")
                else:
                    ruta_video = None
                    if video_file:
                        import config
                        from datetime import datetime
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        nombre_video = f"{timestamp}_{video_file.name}"
                        ruta_video = f"{config.VIDEOS_TUTORIALES_DIR}/{nombre_video}"
                        with open(ruta_video, "wb") as f:
                            f.write(video_file.getbuffer())
                    
                    if agregar_tutorial(user[0], titulo, descripcion, url_youtube, ruta_video):
                        st.success("Tutorial agregado exitosamente!")
                        st.rerun()
                    else:
                        st.error("Error al agregar el tutorial")
        
        st.subheader("Tutoriales Existentes")
        tutoriales = obtener_tutoriales()
        
        if not tutoriales:
            st.info("No hay tutoriales disponibles.")
        else:
            for tut in tutoriales:
                tut_id, titulo, descripcion, url_youtube, ruta_video, fecha_creacion, nombre_profesor, apellido_profesor = tut
                
                with st.expander(f"{titulo} - {fecha_creacion}"):
                    st.write(f"**Descripción:** {descripcion}")
                    st.write(f"**Creado por:** {nombre_profesor} {apellido_profesor}")
                    
                    if url_youtube:
                        st.write("**Video de YouTube:**")
                        video_id = extraer_id_youtube(url_youtube)
                        if video_id:
                            st.video(f"https://www.youtube.com/watch?v={video_id}")
                        else:
                            st.error("URL de YouTube no válida")
                    
                    elif ruta_video and os.path.exists(ruta_video):
                        st.write("**Video subido:**")
                        st.video(ruta_video)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if url_youtube:
                            st.link_button("🔗 Abrir en YouTube", url_youtube)
                        elif ruta_video:
                            with open(ruta_video, "rb") as file:
                                st.download_button(
                                    label="📥 Descargar Video",
                                    data=file,
                                    file_name=os.path.basename(ruta_video),
                                    mime="video/mp4"
                                )
                    with col2:
                        if st.button("🗑️ Eliminar", key=f"eliminar_tut_{tut_id}"):
                            success, message = eliminar_tutorial(tut_id)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
    
    elif category == "Unidades":
        mostrar_unidades_con_secciones()
    
    elif category == "Guías":
        st.title(f"Gestión de {category}")
        
        st.subheader(f"Subir archivos a {category}")
        uploaded_files = st.file_uploader(
            f"Elige archivos para {category}", 
            type=["pdf", "docx", "pptx", "jpg", "png", "jpeg"], 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            if st.button(f"Subir {len(uploaded_files)} archivo(s)"):
                for uploaded_file in uploaded_files:
                    guardar_archivo(user[0], uploaded_file, category)
                st.success(f"Se han subido {len(uploaded_files)} archivos a {category}")
                st.rerun()
        
        st.subheader(f"Archivos en {category}")
        archivos = obtener_archivos(categoria=category)
        
        if not archivos:
            st.write(f"No hay archivos en {category} aún.")
        else:
            if "expanded_pdf" not in st.session_state:
                st.session_state.expanded_pdf = None
            
            for arch in archivos:
                arch_id, nombre_archivo, ruta_archivo, tipo_archivo, fecha_subida, nombre_profesor, apellido_profesor, categoria_archivo, ruta_pdf, seccion_id = arch
                
                with st.expander(f"{nombre_archivo} - {fecha_subida} (Subido por: {nombre_profesor} {apellido_profesor})", 
                                expanded=(st.session_state.expanded_pdf == nombre_archivo)):
                    st.write(f"Tipo: {tipo_archivo}")
                    st.write(f"Categoría: {categoria_archivo}")
                    
                    if tipo_archivo == 'application/pdf':
                        col1, col2 = st.columns([1, 1])
                        with col1:
                            if st.button(f"Ver {nombre_archivo}", key=f"btn_{nombre_archivo}"):
                                st.session_state.expanded_pdf = nombre_archivo
                        with col2:
                            with open(ruta_archivo, "rb") as f:
                                st.download_button(
                                    label="Descargar",
                                    data=f,
                                    file_name=nombre_archivo,
                                    mime="application/pdf",
                                    key=f"download_{nombre_archivo}"
                                )
                        
                        if st.session_state.expanded_pdf == nombre_archivo:
                            try:
                                from streamlit_pdf_viewer import pdf_viewer
                                pdf_viewer(ruta_archivo, height=600)
                            except Exception as e:
                                st.error(f"No se pudo mostrar el PDF: {str(e)}")
                    else:
                        mostrar_vista_previa(ruta_archivo, tipo_archivo, ruta_pdf)
                    
                    col1, col2 = st.columns(2)
                    with col2:
                        if st.button("🗑️ Eliminar", key=f"eliminar_{arch_id}"):
                            success, message = eliminar_archivo(arch_id)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
    elif category == "Revisiones":
        mostrar_revisiones()

def mostrar_cuestionarios_ia():
    st.title("Generador de Cuestionarios con IA")
    user = st.session_state.current_user
    profesor_id = user[0]
    
    # Inicializar variables de estado de manera segura
    if 'quiz_questions' not in st.session_state:
        st.session_state.quiz_questions = None
    if 'quiz_user_answers' not in st.session_state:
        st.session_state.quiz_user_answers = {}
    if 'quiz_pdf_text' not in st.session_state:
        st.session_state.quiz_pdf_text = None
    if 'quiz_file_info' not in st.session_state:
        st.session_state.quiz_file_info = None
    if 'quiz_num_questions' not in st.session_state:
        st.session_state.quiz_num_questions = 5
    if 'quiz_files_uploaded' not in st.session_state:
        st.session_state.quiz_files_uploaded = False
    if 'quiz_show_questions' not in st.session_state:
        st.session_state.quiz_show_questions = False
    if 'quiz_titulo' not in st.session_state:
        st.session_state.quiz_titulo = ""
    if 'selected_files' not in st.session_state:
        st.session_state.selected_files = []
    
    # Pestañas para crear nuevo cuestionario y ver existentes
    tab1, tab2 = st.tabs(["Crear Nuevo Cuestionario", "Mis Cuestionarios"])
    
    with tab1:
        st.subheader("Crear Nuevo Cuestionario")
        
        # Título del cuestionario
        titulo_quiz = st.text_input(
            "Título del cuestionario",
            value=st.session_state.quiz_titulo,
            placeholder="Ej: Cuestionario sobre Matemáticas Básicas",
            key="quiz_titulo_input"
        )
        st.session_state.quiz_titulo = titulo_quiz
        
        # Obtener TODOS los archivos de Unidades (de todos los profesores)
        archivos_unidades = obtener_archivos(categoria="Unidades")
        
        if not archivos_unidades:
            st.info("No hay archivos en 'Unidades'. Sube archivos primero en la sección Unidades para poder generar cuestionarios.")
        else:
            st.subheader("Selecciona los archivos para generar el cuestionario")
            
            # Filtrar solo archivos PDF
            archivos_pdf = [arch for arch in archivos_unidades if arch[3] == 'application/pdf']
            
            if not archivos_pdf:
                st.info("No hay archivos PDF en 'Unidades'. Solo se pueden generar cuestionarios a partir de archivos PDF.")
            else:
                # Inicializar selected_files si no existe
                if 'selected_files' not in st.session_state:
                    st.session_state.selected_files = []
                
                # Mostrar lista de archivos con checkboxes
                st.write(f"**Archivos PDF disponibles en Unidades ({len(archivos_pdf)} archivos):**")
                
                # Agrupar archivos por profesor para mejor organización
                archivos_por_profesor = {}
                for arch in archivos_pdf:
                    arch_id, nombre_archivo, ruta_archivo, tipo_archivo, fecha_subida, nombre_profesor, apellido_profesor, categoria_archivo, ruta_pdf, seccion_id = arch
                    
                    profesor_key = f"{nombre_profesor} {apellido_profesor}"
                    if profesor_key not in archivos_por_profesor:
                        archivos_por_profesor[profesor_key] = []
                    
                    archivos_por_profesor[profesor_key].append(arch)
                
                # Mostrar archivos organizados por profesor
                for profesor, archivos in archivos_por_profesor.items():
                    with st.expander(f"📁 Archivos de {profesor} ({len(archivos)} archivos)"):
                        for arch in archivos:
                            arch_id, nombre_archivo, ruta_archivo, tipo_archivo, fecha_subida, nombre_profesor, apellido_profesor, categoria_archivo, ruta_pdf, seccion_id = arch
                            
                            # Checkbox para seleccionar archivo
                            seleccionado = st.checkbox(
                                f"{nombre_archivo} (Subido: {fecha_subida})",
                                value=arch_id in st.session_state.selected_files,
                                key=f"checkbox_{arch_id}"
                            )
                            
                            if seleccionado and arch_id not in st.session_state.selected_files:
                                st.session_state.selected_files.append(arch_id)
                            elif not seleccionado and arch_id in st.session_state.selected_files:
                                st.session_state.selected_files.remove(arch_id)
                
                # Mostrar resumen de archivos seleccionados
                if st.session_state.selected_files:
                    st.subheader(f"📋 Archivos seleccionados ({len(st.session_state.selected_files)}):")
                    for arch_id in st.session_state.selected_files:
                        # Encontrar el archivo en la lista
                        archivo_seleccionado = next((arch for arch in archivos_pdf if arch[0] == arch_id), None)
                        if archivo_seleccionado:
                            nombre_archivo = archivo_seleccionado[1]
                            profesor_nombre = f"{archivo_seleccionado[5]} {archivo_seleccionado[6]}"
                            st.write(f"• {nombre_archivo} (de {profesor_nombre})")
                    
                    # Botón para limpiar selección
                    if st.button("🗑️ Limpiar selección"):
                        st.session_state.selected_files = []
                        st.rerun()
                else:
                    st.info("Selecciona al menos un archivo PDF para generar el cuestionario.")
            
            # Selector de cantidad de preguntas
            st.subheader("Configuración del cuestionario")
            question_options = [str(i) for i in range(3, 11)]
            selected_question_count = st.selectbox(
                "Selecciona la cantidad de preguntas a generar:",
                options=question_options,
                index=question_options.index(str(st.session_state.quiz_num_questions)) if str(st.session_state.quiz_num_questions) in question_options else 2,
                key="quiz_num_questions_select"
            )
            st.session_state.quiz_num_questions = int(selected_question_count)
            
            # Botón para generar preguntas
            if st.button("🚀 Generar Preguntas", key="generate_quiz_questions", type="primary"):
                if not st.session_state.selected_files:
                    st.error("❌ Selecciona al menos un archivo PDF.")
                elif not st.session_state.quiz_titulo:
                    st.error("❌ Por favor, ingresa un título para el cuestionario.")
                else:
                    with st.spinner(f"📚 Extrayendo texto de {len(st.session_state.selected_files)} PDF(s) y generando {st.session_state.quiz_num_questions} preguntas..."):
                        try:
                            from utils.cuestionarios_ia import extract_text_from_selected_pdfs, generate_questions, parse_questions
                            
                            # Obtener las rutas de los archivos seleccionados
                            rutas_seleccionadas = []
                            file_info_list = []
                            
                            for arch_id in st.session_state.selected_files:
                                archivo = next((arch for arch in archivos_pdf if arch[0] == arch_id), None)
                                if archivo and os.path.exists(archivo[2]):  # Verificar que el archivo existe
                                    arch_id, nombre_archivo, ruta_archivo, tipo_archivo, fecha_subida, nombre_profesor, apellido_profesor, categoria_archivo, ruta_pdf, seccion_id = archivo
                                    rutas_seleccionadas.append(ruta_archivo)
                                    file_info_list.append({
                                        "name": nombre_archivo,
                                        "profesor": f"{nombre_profesor} {apellido_profesor}",
                                        "size": os.path.getsize(ruta_archivo) / (1024*1024) if os.path.exists(ruta_archivo) else 0,
                                        "text_length": 0  # Se calculará en extract_text_from_selected_pdfs
                                    })
                                else:
                                    st.warning(f"El archivo con ID {arch_id} no se encuentra en el sistema.")
                            
                            if not rutas_seleccionadas:
                                st.error("No se pudieron encontrar los archivos seleccionados.")
                                return
                            
                            # Extraer texto de los archivos seleccionados
                            st.session_state.quiz_pdf_text, actual_file_info = extract_text_from_selected_pdfs(rutas_seleccionadas, file_info_list)
                            st.session_state.quiz_file_info = actual_file_info
                            
                            # Generar preguntas
                            raw_questions = generate_questions(
                                st.session_state.quiz_pdf_text, 
                                st.session_state.quiz_num_questions, 
                                st.session_state.quiz_file_info
                            )
                            st.session_state.quiz_questions = parse_questions(raw_questions)
                            st.session_state.quiz_show_questions = True
                            st.session_state.quiz_user_answers = {}
                            
                            # Verificar la cantidad de preguntas generadas
                            if len(st.session_state.quiz_questions) != st.session_state.quiz_num_questions:
                                st.warning(f"Se generaron {len(st.session_state.quiz_questions)} preguntas en lugar de {st.session_state.quiz_num_questions}.")
                            else:
                                st.success(f"✅ ¡Se generaron {len(st.session_state.quiz_questions)} preguntas exitosamente!")
                                
                        except Exception as e:
                            st.error(f"❌ Error al generar preguntas: {str(e)}")
        
        # Mostrar preguntas si ya han sido generadas
        if st.session_state.quiz_show_questions and st.session_state.quiz_questions:
            st.subheader(f"📝 Vista Previa del Cuestionario: '{st.session_state.quiz_titulo}'")
            st.write(f"**Total de preguntas:** {len(st.session_state.quiz_questions)}")
            st.write(f"**Archivos utilizados:** {len(st.session_state.quiz_file_info)}")
            
            for i, q in enumerate(st.session_state.quiz_questions):
                with st.expander(f"Pregunta {i+1}", expanded=True):
                    st.write(f"**{q['question']}**")
                    
                    # Mostrar opciones
                    for key, value in q['options'].items():
                        st.write(f"**{key})** {value}")
                    
                    st.write(f"**Respuesta correcta:** {q['correct']}) {q['options'][q['correct']]}")
            
            # Botones de acción
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("💾 Guardar Cuestionario", key="save_quiz", type="primary"):
                    try:
                        from utils.cuestionarios_ia import save_quiz_to_db
                        save_quiz_to_db(
                            profesor_id, 
                            st.session_state.quiz_titulo, 
                            st.session_state.quiz_questions, 
                            st.session_state.quiz_file_info
                        )
                        st.success(f"✅ ¡Cuestionario '{st.session_state.quiz_titulo}' guardado exitosamente!")
                        
                        # Limpiar estado completamente
                        st.session_state.quiz_questions = None
                        st.session_state.quiz_show_questions = False
                        st.session_state.quiz_titulo = ""
                        st.session_state.quiz_files_uploaded = False
                        st.session_state.quiz_pdf_text = None
                        st.session_state.quiz_file_info = None
                        st.session_state.selected_files = []
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al guardar el cuestionario: {str(e)}")
            with col2:
                if st.button("🔄 Generar Nuevo", key="generate_new"):
                    # Mantener los archivos seleccionados pero regenerar preguntas
                    st.session_state.quiz_questions = None
                    st.session_state.quiz_show_questions = False
                    st.rerun()
            with col3:
                if st.button("🗑️ Limpiar Todo", key="clear_all"):
                    # Limpiar estado completamente
                    st.session_state.quiz_questions = None
                    st.session_state.quiz_show_questions = False
                    st.session_state.quiz_titulo = ""
                    st.session_state.quiz_files_uploaded = False
                    st.session_state.quiz_pdf_text = None
                    st.session_state.quiz_file_info = None
                    st.session_state.selected_files = []
                    st.rerun()
    
    with tab2:
        st.subheader("Mis Cuestionarios Guardados")
        
        try:
            from utils.cuestionarios_ia import get_quizzes_by_profesor, delete_quiz
            quizzes = get_quizzes_by_profesor(profesor_id)
            
            if not quizzes:
                st.info("No tienes cuestionarios guardados.")
            else:
                for quiz in quizzes:
                    with st.expander(f"{quiz['titulo']} - {quiz['fecha_creacion']} ({len(quiz['preguntas'])} preguntas)"):
                        st.write(f"**Archivos utilizados:**")
                        for file in quiz['file_info']:
                            st.write(f"- {file['name']} ({file['size']:.2f} MB)")
                        
                        st.write("---")
                        st.write("**Preguntas:**")
                        
                        for i, q in enumerate(quiz['preguntas']):
                            st.write(f"**Pregunta {i+1}:** {q['question']}")
                            for key, value in q['options'].items():
                                st.write(f"{key}) {value}")
                            st.write(f"**Respuesta correcta:** {q['correct']}) {q['options'][q['correct']]}")
                            st.write("---")
                        
                        # Botón para eliminar cuestionario
                        if st.button("Eliminar Cuestionario", key=f"delete_quiz_{quiz['id']}"):
                            delete_quiz(quiz['id'])
                            st.success("Cuestionario eliminado exitosamente!")
                            st.rerun()
        except Exception as e:
            st.error(f"Error al cargar los cuestionarios: {str(e)}")