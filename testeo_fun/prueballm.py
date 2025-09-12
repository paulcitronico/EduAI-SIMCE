import streamlit as st
import pdfplumber
from openai import OpenAI
import re

# Configuración del cliente de NVIDIA
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

# Función para extraer texto del PDF
def extract_text_from_pdf(uploaded_files):
    text = ""
    file_info = []
    
    for uploaded_file in uploaded_files:
        file_text = ""
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    file_text += page_text + "\n"
        
        # Agregar información del archivo al texto
        text += f"=== INICIO DEL DOCUMENTO: {uploaded_file.name} ===\n"
        text += file_text + "\n"
        text += f"=== FIN DEL DOCUMENTO: {uploaded_file.name} ===\n\n"
        
        file_info.append({
            "name": uploaded_file.name,
            "size": uploaded_file.size / (1024*1024),
            "text_length": len(file_text)
        })
    
    return text, file_info

# Función para generar preguntas usando el modelo de NVIDIA
def generate_questions(text, num_questions, file_info):
    # Crear un prompt más detallado
    prompt = f"""
    Basado en los siguientes documentos, genera exactamente {num_questions} preguntas de opción múltiple con 4 alternativas cada una.
    
    INSTRUCCIONES IMPORTANTES:
    1. Debes generar EXACTAMENTE {num_questions} preguntas, ni más ni menos.
    2. Las preguntas deben cubrir el contenido de TODOS los documentos proporcionados.
    3. Asegúrate de distribuir las preguntas de manera equitativa entre todos los documentos.
    4. Formato de salida para cada pregunta:
       Pregunta: [texto de la pregunta]
       A) [alternativa A]
       B) [alternativa B]
       C) [alternativa C]
       D) [alternativa D]
       Respuesta correcta: [letra de la alternativa correcta]
    
    Documentos proporcionados:
    {text}
    """
    
    completion = client.chat.completions.create(
        model="nvidia/nvidia-nemotron-nano-9b-v2",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        top_p=0.7,
        max_tokens=8192,
        extra_body={"chat_template_kwargs": {"thinking": True}},
        stream=True
    )
    
    full_response = ""
    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            full_response += chunk.choices[0].delta.content
    
    return full_response

# Función para parsear las preguntas generadas
def parse_questions(response):
    questions = []
    # Patrón mejorado para capturar preguntas y opciones
    pattern = r'Pregunta:\s*(.*?)\n\s*A\)\s*(.*?)\n\s*B\)\s*(.*?)\n\s*C\)\s*(.*?)\n\s*D\)\s*(.*?)\n\s*Respuesta correcta:\s*([ABCD])'
    matches = re.findall(pattern, response, re.DOTALL)
    
    for match in matches:
        question, a, b, c, d, correct = match
        questions.append({
            "question": question.strip(),
            "options": {
                "A": a.strip(),
                "B": b.strip(),
                "C": c.strip(),
                "D": d.strip()
            },
            "correct": correct.upper()
        })
    
    return questions

# Función para generar retroalimentación
def generate_feedback(questions, user_answers):
    prompt = "Basado en las siguientes preguntas y respuestas del usuario, genera una retroalimentación detallada:\n\n"
    
    for i, q in enumerate(questions):
        prompt += f"Pregunta {i+1}: {q['question']}\n"
        prompt += f"Opciones:\n"
        for key, value in q['options'].items():
            prompt += f"{key}) {value}\n"
        prompt += f"Respuesta correcta: {q['correct']}\n"
        prompt += f"Respuesta del usuario: {user_answers[i]}\n\n"
    
    completion = client.chat.completions.create(
        model="deepseek-ai/deepseek-v3.1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        top_p=0.7,
        max_tokens=8192,
        extra_body={"chat_template_kwargs": {"thinking": True}},
        stream=True
    )
    
    full_response = ""
    for chunk in completion:
        if chunk.choices[0].delta.content is not None:
            full_response += chunk.choices[0].delta.content
    
    return full_response

# Interfaz de Streamlit
st.title("Generador de Cuestionarios con Retroalimentación")
st.write("Sube uno o más archivos PDF para generar un cuestionario con alternativas.")

# Inicializar variables de estado
if 'questions' not in st.session_state:
    st.session_state.questions = None
if 'user_answers' not in st.session_state:
    st.session_state.user_answers = {}
if 'pdf_text' not in st.session_state:
    st.session_state.pdf_text = None
if 'file_info' not in st.session_state:
    st.session_state.file_info = None
if 'num_questions' not in st.session_state:
    st.session_state.num_questions = 5
if 'files_uploaded' not in st.session_state:
    st.session_state.files_uploaded = False
if 'show_questions' not in st.session_state:
    st.session_state.show_questions = False

# Subida de múltiples archivos PDF
uploaded_files = st.file_uploader(
    "Sube uno o más archivos PDF",
    type=["pdf"],
    accept_multiple_files=True
)

# Si se suben archivos, extraer texto solo una vez
if uploaded_files:
    if not st.session_state.files_uploaded:
        with st.spinner("Extrayendo texto de los PDFs..."):
            st.session_state.pdf_text, st.session_state.file_info = extract_text_from_pdf(uploaded_files)
            st.session_state.files_uploaded = True
    
    # Mostrar información de los archivos subidos
    st.write(f"Se han subido {len(uploaded_files)} archivos PDF:")
    for file in st.session_state.file_info:
        st.write(f"- {file['name']} ({file['size']:.2f} MB, {file['text_length']} caracteres)")
    
    # Selector de cantidad de preguntas (select en lugar de slider) - Cambiado a máximo 10
    question_options = [str(i) for i in range(3, 11)]  # De 3 a 10 preguntas
    default_index = question_options.index(str(st.session_state.num_questions)) if str(st.session_state.num_questions) in question_options else 2
    
    st.session_state.num_questions = int(st.selectbox(
        "Selecciona la cantidad de preguntas a generar:",
        options=question_options,
        index=default_index
    ))
    
    # Botón para generar preguntas - siempre visible después de subir archivos
    if st.button("Generar Preguntas"):
        if st.session_state.pdf_text:
            with st.spinner(f"Generando {st.session_state.num_questions} preguntas..."):
                raw_questions = generate_questions(st.session_state.pdf_text, st.session_state.num_questions, st.session_state.file_info)
                st.session_state.questions = parse_questions(raw_questions)
                st.session_state.show_questions = True
                # Reiniciar respuestas
                st.session_state.user_answers = {}
                
                # Verificar la cantidad de preguntas generadas
                if len(st.session_state.questions) != st.session_state.num_questions:
                    st.warning(f"Se generaron {len(st.session_state.questions)} preguntas en lugar de {st.session_state.num_questions}.")
                    
                    # Si faltan preguntas, intentar generar las faltantes
                    if len(st.session_state.questions) < st.session_state.num_questions:
                        missing = st.session_state.num_questions - len(st.session_state.questions)
                        st.info(f"Intentando generar las {missing} preguntas faltantes...")
                        
                        # Generar preguntas adicionales
                        additional_raw = generate_questions(st.session_state.pdf_text, missing, st.session_state.file_info)
                        additional_questions = parse_questions(additional_raw)
                        
                        # Agregar las preguntas adicionales
                        st.session_state.questions.extend(additional_questions)
                        st.info(f"Ahora hay {len(st.session_state.questions)} preguntas en total.")
        else:
            st.error("No se pudo extraer texto de los PDFs. Por favor, intenta con otros archivos.")

# Mostrar preguntas si ya han sido generadas
if st.session_state.show_questions and st.session_state.questions:
    st.subheader(f"Cuestionario ({len(st.session_state.questions)} preguntas)")
    
    for i, q in enumerate(st.session_state.questions):
        st.write(f"**Pregunta {i+1}:** {q['question']}")
        
        # Crear un único radio button para todas las opciones
        options = [f"{key}) {value}" for key, value in q['options'].items()]
        
        # Obtener la respuesta actual del usuario (si existe)
        current_answer = st.session_state.user_answers.get(f"q{i}", None)
        
        # Mostrar el radio button con las opciones
        selected_option = st.radio(
            f"Selecciona una opción para la pregunta {i+1}",
            options=options,
            index=options.index(current_answer) if current_answer in options else None,
            key=f"q{i}"
        )
        
        # Guardar la respuesta seleccionada
        if selected_option:
            # Extraer la letra de la opción seleccionada (A, B, C, D)
            selected_letter = selected_option.split(')')[0]
            st.session_state.user_answers[f"q{i}"] = selected_option
        
        st.write("---")  # Separador entre preguntas
    
    # Botón para generar retroalimentación
    if st.button("Generar Retroalimentación"):
        # Verificar que todas las preguntas han sido respondidas
        all_answered = all(f"q{i}" in st.session_state.user_answers for i in range(len(st.session_state.questions)))
        
        if not all_answered:
            st.warning("Por favor responde todas las preguntas antes de generar la retroalimentación.")
        else:
            # Preparar las respuestas del usuario para la retroalimentación
            user_answers_list = []
            for i in range(len(st.session_state.questions)):
                answer_text = st.session_state.user_answers[f"q{i}"]
                # Extraer solo la letra (A, B, C, D)
                answer_letter = answer_text.split(')')[0]
                user_answers_list.append(answer_letter)
            
            with st.spinner("Generando retroalimentación..."):
                feedback = generate_feedback(st.session_state.questions, user_answers_list)
            
            st.subheader("Retroalimentación")
            
            # Mostrar retroalimentación detallada con indicadores de correcto/incorrecto
            for i, q in enumerate(st.session_state.questions):
                is_correct = user_answers_list[i] == q['correct']
                status = "¡Correcto! ✅" if is_correct else "Incorrecto ❌"
                
                st.markdown(f"### Pregunta {i+1}: {status}")
                st.write(f"**Pregunta:** {q['question']}")
                st.write(f"**Tu respuesta:** {user_answers_list[i]}) {q['options'][user_answers_list[i]]}")
                st.write(f"**Respuesta correcta:** {q['correct']}) {q['options'][q['correct']]}")
                
                if not is_correct:
                    st.write(f"**Explicación:** {feedback.split(f'Pregunta {i+1}:')[-1].split(f'Pregunta {i+2}:')[0] if f'Pregunta {i+1}:' in feedback else feedback}")
                
                st.write("---")
            
            # Mostrar resumen
            correct_count = sum(1 for i in range(len(st.session_state.questions)) if user_answers_list[i] == st.session_state.questions[i]['correct'])
            st.success(f"Has respondido correctamente {correct_count} de {len(st.session_state.questions)} preguntas ({correct_count/len(st.session_state.questions)*100:.1f}%)")

# Botón para reiniciar el proceso
if st.session_state.files_uploaded or st.session_state.show_questions:
    if st.button("Reiniciar Proceso"):
        # Limpiar todas las variables de estado
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        
        # Reinicializar variables esenciales
        st.session_state.questions = None
        st.session_state.user_answers = {}
        st.session_state.pdf_text = None
        st.session_state.file_info = None
        st.session_state.num_questions = 5
        st.session_state.files_uploaded = False
        st.session_state.show_questions = False
        
        # Recargar la aplicación
        st.rerun()