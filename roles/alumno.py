import streamlit as st
from database.operations import add_user, verify_user
from auth.email_service import send_email
import os
from datetime import datetime
from database.operations import obtener_archivos, obtener_tutoriales
from streamlit_pdf_viewer import pdf_viewer
from utils.file_processing import extraer_id_youtube
from utils.preview_utils import mostrar_vista_previa

from database.operations import obtener_secciones
from utils.common import logout



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
                    from main import go_to_login
                    go_to_login()
                else:
                    st.error("El nombre de usuario o email ya están en uso")
    
    st.markdown("---")
    if st.button("¿Ya tienes cuenta? Inicia sesión"):
        from main import go_to_login
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
            from main import go_to_login
            
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
        from main import go_to_login
        go_to_login()

def reset_password_confirm_page():
    st.title("Restablecer Contraseña")
    token = st.session_state.reset_token
    
    if st.session_state.password_reset_success:
        st.success("¡Contraseña restablecida exitosamente!")
        st.write("Ya puedes iniciar sesión con tu nueva contraseña.")
        
        if st.button("¿Ya tienes cuenta? Inicia sesión"):
            st.session_state.password_reset_success = False
            from main import go_to_login
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
        from main import go_to_login
        go_to_login()

def alumno_sidebar():
    # Barra lateral simplificada
    user = st.session_state.current_user
    st.sidebar.image(user[6] if user[6] else "https://via.placeholder.com/150", width=150)
    st.sidebar.write(f"**{user[2]} {user[3]}**")
    st.sidebar.write(f"Rol: {user[7]}")
    
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Cerrar Sesión"):
        logout()

def alumno_page():
    user = st.session_state.current_user
    
    # Mostrar barra lateral simplificada
    alumno_sidebar()
    
    # Contenido principal
    st.title(f"Bienvenido, {user[2]} {user[3]}")
    
    # Barra de navegación en el contenido principal
    st.subheader("Navegación")
    col1, col2, col3, col4, col5 = st.columns(5)
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
    
    # Contenido según la categoría seleccionada
    category = st.session_state.selected_category
    
    if category == "Cuestionarios IA":
        mostrar_cuestionarios_para_alumnos()

    elif category == "Tutoriales":
        st.title("Tutoriales")
        tutoriales = obtener_tutoriales()
        
        if not tutoriales:
            st.info("No hay tutoriales disponibles.")
        else:
            for tut in tutoriales:
                tut_id, titulo, descripcion, url_youtube, ruta_video, fecha_creacion, nombre_profesor, apellido_profesor = tut
                
                with st.expander(f"{titulo} - {fecha_creacion}"):
                    st.write(f"**Descripción:** {descripcion}")
                    st.write(f"**Creado por:** {nombre_profesor} {apellido_profesor}")
                    
                    # Mostrar video según el tipo
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
                    
                    # Botón de descarga si es un video subido
                    if ruta_video and os.path.exists(ruta_video):
                        with open(ruta_video, "rb") as file:
                            st.download_button(
                                label="📥 Descargar Video",
                                data=file,
                                file_name=os.path.basename(ruta_video),
                                mime="video/mp4"
                            )
    
    elif category == "Unidades":
        # Mostrar unidades con secciones para alumnos
        mostrar_unidades_para_alumnos()
    elif category == "Revisiones":
        # Mostrar historial de revisiones para alumnos
        mostrar_revisiones_para_alumnos()
    else:  # Para Guías
        st.title(f"{category}")
        # Obtener todos los archivos de la categoría (de todos los profesores)
        archivos = obtener_archivos(categoria=category)  # Sin filtrar por profesor_id
        
        if not archivos:
            st.write(f"No hay archivos en {category} aún.")
        else:
            # Control de expansión: solo uno a la vez
            if "expanded_pdf" not in st.session_state:
                st.session_state.expanded_pdf = None
            
            for arch in archivos:
                arch_id, nombre_archivo, ruta_archivo, tipo_archivo, fecha_subida, nombre_profesor, apellido_profesor, categoria_archivo, ruta_pdf, seccion_id = arch
                
                # Crear expander para cada archivo
                with st.expander(f"{nombre_archivo} - {fecha_subida} (Subido por: {nombre_profesor} {apellido_profesor})", 
                                expanded=(st.session_state.expanded_pdf == nombre_archivo)):
                    st.write(f"Tipo: {tipo_archivo}")
                    st.write(f"Categoría: {categoria_archivo}")
                    
                    # Vista previa mejorada para PDFs
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
                                pdf_viewer(ruta_archivo, height=600)
                            except Exception as e:
                                st.error(f"No se pudo mostrar el PDF: {str(e)}")
                    else:
                        # Para otros tipos de archivos, usar la vista previa existente
                        mostrar_vista_previa(ruta_archivo, tipo_archivo, ruta_pdf)
                    

def mostrar_unidades_para_alumnos():
    categoria = "Unidades"
    
    st.title(f"{categoria}")
    
    # Obtener todas las secciones de la categoría
    secciones = obtener_secciones(categoria=categoria)
    
    # Obtener todos los archivos de la categoría
    todos_los_archivos = obtener_archivos(categoria=categoria)
    
    # Organizar archivos por sección
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
    
    # Mostrar cada sección con sus archivos
    for seccion in secciones:
        seccion_id, nombre_seccion, created_at, nombre_profesor_seccion, apellido_profesor_seccion = seccion
        
        with st.container():
            st.markdown(f"### {nombre_seccion}")
            st.write(f"Creada por: {nombre_profesor_seccion} {apellido_profesor_seccion} - {created_at}")
            
            # Mostrar archivos de esta sección
            if seccion_id in archivos_por_seccion and archivos_por_seccion[seccion_id]:
                st.subheader(f"Archivos en {nombre_seccion}")
                
                for archivo in archivos_por_seccion[seccion_id]:
                    arch_id, nombre_archivo, ruta_archivo, tipo_archivo, fecha_subida, nombre_profesor, apellido_profesor, categoria_archivo, ruta_pdf, archivo_seccion_id = archivo
                    
                    with st.expander(f"{nombre_archivo} - {fecha_subida} (Subido por: {nombre_profesor} {apellido_profesor})"):
                        st.write(f"Tipo: {tipo_archivo}")
                        
                        # Vista previa mejorada para PDFs
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
                            
                            # Verificar si expanded_pdf existe antes de usarlo
                            if 'expanded_pdf' in st.session_state and st.session_state.expanded_pdf == nombre_archivo:
                                try:
                                    pdf_viewer(ruta_archivo, height=600)
                                except Exception as e:
                                    st.error(f"No se pudo mostrar el PDF: {str(e)}")
                        else:
                            # Para otros tipos de archivos, usar la vista previa existente
                            mostrar_vista_previa(ruta_archivo, tipo_archivo, ruta_pdf)
                        

            else:
                st.info(f"No hay archivos en {nombre_seccion}")
            
            st.markdown("---")
    
    # Mostrar archivos sin sección
    if archivos_sin_seccion:
        st.subheader("Otros Archivos")
        
        for archivo in archivos_sin_seccion:
            arch_id, nombre_archivo, ruta_archivo, tipo_archivo, fecha_subida, nombre_profesor, apellido_profesor, categoria_archivo, ruta_pdf, seccion_id = archivo
            
            with st.expander(f"{nombre_archivo} - {fecha_subida} (Subido por: {nombre_profesor} {apellido_profesor})"):
                st.write(f"Tipo: {tipo_archivo}")
                
                # Vista previa mejorada para PDFs
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
                    
                    # Verificar si expanded_pdf existe antes de usarlo
                    if 'expanded_pdf' in st.session_state and st.session_state.expanded_pdf == nombre_archivo:
                        try:
                            pdf_viewer(ruta_archivo, height=600)
                        except Exception as e:
                            st.error(f"No se pudo mostrar el PDF: {str(e)}")
                else:
                    # Para otros tipos de archivos, usar la vista previa existente
                    mostrar_vista_previa(ruta_archivo, tipo_archivo, ruta_pdf)
                

def mostrar_cuestionarios_para_alumnos():
    st.title("Cuestionarios IA - Realizar Evaluación")
    
    # Reiniciar estados si venimos de otra sección
    if st.session_state.selected_category == "Cuestionarios IA":
        if 'quiz_completed' in st.session_state and st.session_state.quiz_completed:
            st.session_state.quiz_completed = False
            st.session_state.quiz_show_questions = False
            st.session_state.current_quiz = None
    
    # Inicializar variables de estado
    if 'quiz_questions' not in st.session_state:
        st.session_state.quiz_questions = None
    if 'quiz_user_answers' not in st.session_state:
        st.session_state.quiz_user_answers = {}
    if 'quiz_show_questions' not in st.session_state:
        st.session_state.quiz_show_questions = False
    if 'current_quiz' not in st.session_state:
        st.session_state.current_quiz = None
    if 'quiz_completed' not in st.session_state:
        st.session_state.quiz_completed = False
    
    # Obtener todos los cuestionarios disponibles
    try:
        import sqlite3
        import json
        
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        # Verificar si la tabla existe
        c.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='cuestionarios_ia'
        ''')
        table_exists = c.fetchone()
        
        if not table_exists:
            st.info("No hay cuestionarios disponibles en este momento.")
            conn.close()
            return
        
        # Obtener cuestionarios con información del profesor
        c.execute('''
            SELECT c.id, c.titulo, c.preguntas, c.file_info, c.fecha_creacion, 
                   u.nombre, u.apellido
            FROM cuestionarios_ia c
            JOIN users u ON c.profesor_id = u.id
            ORDER BY c.fecha_creacion DESC
        ''')
        
        quizzes = c.fetchall()
        conn.close()
        
        if not quizzes:
            st.info("No hay cuestionarios disponibles en este momento.")
            return
        
        # Mostrar lista de cuestionarios disponibles
        st.subheader("Cuestionarios Disponibles")
        
        for quiz in quizzes:
            quiz_id, titulo, preguntas_json, file_info_json, fecha, nombre_prof, apellido_prof = quiz
            
            # CORRECCIÓN: Usar container en lugar de expander con key
            with st.container():
                st.markdown(f"**{titulo}** - Por: {nombre_prof} {apellido_prof} ({fecha})")
                
                # Mostrar información del cuestionario
                file_info = json.loads(file_info_json) if file_info_json else []
                st.write(f"Archivos utilizados: {len(file_info)} archivos")
                st.write(f"Número de preguntas: {len(json.loads(preguntas_json))}")
                
                # Botón para comenzar el cuestionario
                if st.button("Comenzar Cuestionario", key=f"start_quiz_{quiz_id}"):
                    st.session_state.current_quiz = {
                        'id': quiz_id,
                        'titulo': titulo,
                        'preguntas': json.loads(preguntas_json),
                        'profesor': f"{nombre_prof} {apellido_prof}"
                    }
                    st.session_state.quiz_questions = json.loads(preguntas_json)
                    st.session_state.quiz_show_questions = True
                    st.session_state.quiz_user_answers = {}
                    st.rerun()
                
                st.markdown("---")
        
        # Mostrar cuestionario si se ha seleccionado uno
        if st.session_state.quiz_show_questions and st.session_state.quiz_questions:
            st.subheader(f"Cuestionario: {st.session_state.current_quiz['titulo']}")
            st.write(f"Profesor: {st.session_state.current_quiz['profesor']}")
            st.write("---")
            
            # Formulario para el cuestionario
            with st.form("quiz_form"):
                for i, q in enumerate(st.session_state.quiz_questions):
                    st.write(f"**Pregunta {i+1}:** {q['question']}")
                    
                    # Crear radio buttons para las opciones
                    options = [f"{key}) {value}" for key, value in q['options'].items()]
                    selected_option = st.radio(
                        f"Selecciona una opción para la pregunta {i+1}",
                        options=options,
                        key=f"quiz_q_{i}"
                    )
                    
                    # Guardar la respuesta seleccionada
                    if selected_option:
                        st.session_state.quiz_user_answers[f"q{i}"] = selected_option
                    
                    st.write("---")
                
                # Botón para enviar el cuestionario
                submitted = st.form_submit_button("📤 Finalizar y Ver Resultados")
                
                if submitted:
                    # Verificar que todas las preguntas han sido respondidas
                    all_answered = all(f"q{i}" in st.session_state.quiz_user_answers 
                                     for i in range(len(st.session_state.quiz_questions)))
                    
                    if not all_answered:
                        st.error("❌ Por favor responde todas las preguntas antes de finalizar.")
                    else:
                        # Preparar las respuestas del usuario
                        user_answers_list = []
                        for i in range(len(st.session_state.quiz_questions)):
                            answer_text = st.session_state.quiz_user_answers[f"q{i}"]
                            answer_letter = answer_text.split(')')[0]
                            user_answers_list.append(answer_letter)
                        
                        with st.spinner("🔄 Generando retroalimentación y guardando resultados..."):
                            try:
                                from utils.cuestionarios_ia import generate_feedback, guardar_revision_estudiante
                                
                                # Calcular puntaje
                                correct_count = 0
                                for i, q in enumerate(st.session_state.quiz_questions):
                                    if user_answers_list[i] == q['correct']:
                                        correct_count += 1
                                
                                # Generar retroalimentación
                                feedback = generate_feedback(st.session_state.quiz_questions, user_answers_list)
                                
                                # Guardar la revisión
                                success = guardar_revision_estudiante(
                                    st.session_state.current_user[0],
                                    st.session_state.current_quiz['id'],
                                    st.session_state.current_quiz['titulo'],
                                    user_answers_list,
                                    feedback,
                                    correct_count,
                                    len(st.session_state.quiz_questions)
                                )
                                
                                if success:
                                    # Limpiar estado y redirigir
                                    st.session_state.quiz_completed = True
                                    st.session_state.quiz_show_questions = False
                                    st.session_state.current_quiz = None
                                    st.session_state.quiz_questions = None
                                    st.session_state.quiz_user_answers = {}
                                    st.session_state.selected_category = "Revisiones"
                                    
                                    st.success("✅ ¡Cuestionario completado! Redirigiendo a Revisiones...")
                                    st.rerun()
                                else:
                                    st.error("❌ Error al guardar los resultados. Intenta nuevamente.")
                                    
                            except Exception as e:
                                st.error(f"❌ Error al procesar el cuestionario: {str(e)}")
    
    except Exception as e:
        st.error(f"Error al cargar los cuestionarios: {str(e)}")

# En la función mostrar_revisiones_para_alumnos, corregir el expander
def mostrar_revisiones_para_alumnos():
    st.title("📚 Mis Revisiones de Cuestionarios")
    
    # Obtener el ID del estudiante actual
    estudiante_id = st.session_state.current_user[0]
    
    # Obtener las revisiones del estudiante
    from utils.cuestionarios_ia import obtener_revisiones_estudiante
    revisiones = obtener_revisiones_estudiante(estudiante_id)
    
    if not revisiones:
        st.info("Aún no has completado ningún cuestionario. Realiza un cuestionario en la sección 'Cuestionarios IA' para ver tus revisiones aquí.")
        return
    
    # Mostrar estadísticas generales
    total_cuestionarios = len(revisiones)
    promedio_porcentaje = sum(rev['porcentaje'] for rev in revisiones) / total_cuestionarios
    mejor_resultado = max(rev['porcentaje'] for rev in revisiones)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Cuestionarios", total_cuestionarios)
    with col2:
        st.metric("Promedio General", f"{promedio_porcentaje:.1f}%")
    with col3:
        st.metric("Mejor Resultado", f"{mejor_resultado:.1f}%")
    
    st.markdown("---")
    
    # Mostrar lista de revisiones
    st.subheader("Historial de Cuestionarios")
    
    for i, revision in enumerate(revisiones):
        # CORRECCIÓN: Usar un contenedor en lugar de expander con key
        with st.container():
            st.markdown(f"### {revision['titulo']}")
            st.markdown(f"**Fecha:** {revision['fecha_realizacion']} | **Puntaje:** {revision['puntaje']}/{revision['total_preguntas']} | **Porcentaje:** {revision['porcentaje']:.1f}%")
            
            # Mostrar resumen de retroalimentación
            st.write("**Resumen de Retroalimentación:**")
            feedback_preview = revision['retroalimentacion'][:300] + "..." if len(revision['retroalimentacion']) > 300 else revision['retroalimentacion']
            st.write(feedback_preview)
            
            # Botón para ver detalles completos
            if st.button("📖 Ver Detalles Completos", key=f"detalles_{revision['id']}"):
                # Mostrar detalles completos de esta revisión
                mostrar_detalles_revision(revision)
            
            st.markdown("---")

# Agregar esta nueva función para mostrar detalles de revisión
def mostrar_detalles_revision(revision):
    st.subheader(f"📊 Detalles del Cuestionario: {revision['titulo']}")
    
    # Mostrar resumen general
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Puntaje Final", f"{revision['puntaje']}/{revision['total_preguntas']}")
    with col2:
        st.metric("Porcentaje", f"{revision['porcentaje']:.1f}%")
    
    st.markdown("---")
    
    # Mostrar retroalimentación completa
    st.subheader("📝 Retroalimentación Completa")
    st.write(revision['retroalimentacion'])
    
    st.markdown("---")
    
    # Botón para volver
    if st.button("⬅️ Volver al Historial"):
        st.rerun()
    