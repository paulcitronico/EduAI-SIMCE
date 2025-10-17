# utils/cuestionarios_ia.py
import streamlit as st
import pdfplumber
from openai import OpenAI
import re
import sqlite3
from datetime import datetime
import os

# Configuración del cliente de NVIDIA
client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key="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"
)

# Función para extraer texto del PDF
# En utils/cuestionarios_ia.py, mejora la función extract_text_from_pdf:
# En utils/cuestionarios_ia.py, mejora la función extract_text_from_pdf:
def extract_text_from_pdf(uploaded_files):
    text = ""
    file_info = []
    
    for uploaded_file in uploaded_files:
        file_text = ""
        try:
            with pdfplumber.open(uploaded_file) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            file_text += f"--- Página {page_num + 1} ---\n"
                            file_text += page_text + "\n\n"
                    except Exception as e:
                        print(f"Error en página {page_num + 1}: {str(e)}")
                        # Continuar con la siguiente página
                        continue
        except Exception as e:
            print(f"Error al abrir PDF {uploaded_file.name}: {str(e)}")
            # Agregar un mensaje de error al texto
            file_text = f"Error al procesar el archivo {uploaded_file.name}: {str(e)}\n"
        
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

# Función para guardar cuestionario en la base de datos
def save_quiz_to_db(profesor_id, titulo, questions, file_info):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    # Crear tabla si no existe
    c.execute('''
        CREATE TABLE IF NOT EXISTS cuestionarios_ia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            profesor_id INTEGER NOT NULL,
            titulo TEXT NOT NULL,
            preguntas TEXT NOT NULL,
            file_info TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (profesor_id) REFERENCES users(id)
        )
    ''')
    
    # Convertir preguntas y file_info a JSON
    import json
    preguntas_json = json.dumps(questions)
    file_info_json = json.dumps(file_info)
    
    # Insertar cuestionario
    c.execute('''
        INSERT INTO cuestionarios_ia (profesor_id, titulo, preguntas, file_info)
        VALUES (?, ?, ?, ?)
    ''', (profesor_id, titulo, preguntas_json, file_info_json))
    
    conn.commit()
    conn.close()

# Función para obtener cuestionarios de un profesor
def get_quizzes_by_profesor(profesor_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT id, titulo, preguntas, file_info, fecha_creacion
        FROM cuestionarios_ia
        WHERE profesor_id = ?
        ORDER BY fecha_creacion DESC
    ''', (profesor_id,))
    
    quizzes = c.fetchall()
    conn.close()
    
    # Convertir JSON de vuelta a objetos Python
    import json
    processed_quizzes = []
    for quiz in quizzes:
        quiz_id, titulo, preguntas_json, file_info_json, fecha = quiz
        processed_quizzes.append({
            'id': quiz_id,
            'titulo': titulo,
            'preguntas': json.loads(preguntas_json),
            'file_info': json.loads(file_info_json) if file_info_json else [],
            'fecha_creacion': fecha
        })
    
    return processed_quizzes

# Función para eliminar cuestionario
def delete_quiz(quiz_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute("DELETE FROM cuestionarios_ia WHERE id = ?", (quiz_id,))
    conn.commit()
    conn.close()

def extract_text_from_selected_pdfs(file_paths, file_info):
    """
    Extrae texto de archivos PDF seleccionados desde el sistema de archivos
    """
    text = ""
    updated_file_info = []
    
    for i, file_path in enumerate(file_paths):
        file_text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            file_text += f"--- Página {page_num + 1} ---\n"
                            file_text += page_text + "\n\n"
                    except Exception as e:
                        print(f"Error en página {page_num + 1}: {str(e)}")
                        continue
        except Exception as e:
            print(f"Error al abrir PDF {file_path}: {str(e)}")
            file_text = f"Error al procesar el archivo {os.path.basename(file_path)}: {str(e)}\n"
        
        # Agregar información del archivo al texto
        text += f"=== INICIO DEL DOCUMENTO: {os.path.basename(file_path)} ===\n"
        text += file_text + "\n"
        text += f"=== FIN DEL DOCUMENTO: {os.path.basename(file_path)} ===\n\n"
        
        # Actualizar file_info con la longitud real del texto
        updated_info = file_info[i].copy()
        updated_info["text_length"] = len(file_text)
        updated_file_info.append(updated_info)
    
    return text, updated_file_info

# En cuestionarios_ia.py, agregar estas funciones al final del archivo

def guardar_revision_estudiante(estudiante_id, cuestionario_id, titulo_cuestionario, respuestas_usuario, retroalimentacion, puntaje, total_preguntas):
    """Guarda la revisión de un cuestionario completado por un estudiante"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    import json
    respuestas_json = json.dumps(respuestas_usuario)
    
    c.execute('''
        INSERT INTO revisiones_cuestionarios 
        (estudiante_id, cuestionario_id, titulo_cuestionario, respuestas_usuario, retroalimentacion, puntaje, total_preguntas)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (estudiante_id, cuestionario_id, titulo_cuestionario, respuestas_json, retroalimentacion, puntaje, total_preguntas))
    
    conn.commit()
    conn.close()
    return True

def obtener_revisiones_estudiante(estudiante_id):
    """Obtiene todas las revisiones de un estudiante"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT id, cuestionario_id, titulo_cuestionario, respuestas_usuario, 
               retroalimentacion, puntaje, total_preguntas, fecha_realizacion
        FROM revisiones_cuestionarios 
        WHERE estudiante_id = ?
        ORDER BY fecha_realizacion DESC
    ''', (estudiante_id,))
    
    revisiones = c.fetchall()
    conn.close()
    
    # Convertir JSON de vuelta a objetos Python
    import json
    processed_revisiones = []
    for rev in revisiones:
        rev_id, cuestionario_id, titulo, respuestas_json, retroalimentacion, puntaje, total_preguntas, fecha = rev
        processed_revisiones.append({
            'id': rev_id,
            'cuestionario_id': cuestionario_id,
            'titulo': titulo,
            'respuestas_usuario': json.loads(respuestas_json) if respuestas_json else [],
            'retroalimentacion': retroalimentacion,
            'puntaje': puntaje,
            'total_preguntas': total_preguntas,
            'fecha_realizacion': fecha,
            'porcentaje': (puntaje / total_preguntas) * 100 if total_preguntas > 0 else 0
        })
    
    return processed_revisiones

def obtener_revision_detalle(revision_id):
    """Obtiene los detalles de una revisión específica"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute('''
        SELECT id, cuestionario_id, titulo_cuestionario, respuestas_usuario, 
               retroalimentacion, puntaje, total_preguntas, fecha_realizacion
        FROM revisiones_cuestionarios 
        WHERE id = ?
    ''', (revision_id,))
    
    revision = c.fetchone()
    conn.close()
    
    if revision:
        import json
        rev_id, cuestionario_id, titulo, respuestas_json, retroalimentacion, puntaje, total_preguntas, fecha = revision
        return {
            'id': rev_id,
            'cuestionario_id': cuestionario_id,
            'titulo': titulo,
            'respuestas_usuario': json.loads(respuestas_json) if respuestas_json else [],
            'retroalimentacion': retroalimentacion,
            'puntaje': puntaje,
            'total_preguntas': total_preguntas,
            'fecha_realizacion': fecha,
            'porcentaje': (puntaje / total_preguntas) * 100 if total_preguntas > 0 else 0
        }
    
    return None