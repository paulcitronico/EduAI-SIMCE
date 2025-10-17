import secrets
from datetime import datetime, timedelta
from database.operations import hash_password
from auth.email_service import send_email
import sqlite3

def generate_reset_token(email):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute("SELECT id, nombre FROM users WHERE LOWER(email) = LOWER(?)", (email,))
    user = c.fetchone()
    
    if not user:
        conn.close()
        return False, "El correo electrónico no está registrado en el sistema."
    
    user_id, nombre = user
    
    token = secrets.token_urlsafe(32)
    expiration = datetime.now() + timedelta(hours=1)
    
    expiration_str = expiration.isoformat()
    c.execute("UPDATE users SET reset_token = ?, reset_token_expiration = ? WHERE id = ?", 
              (token, expiration_str, user_id))
    conn.commit()
    conn.close()
    
    subject = "Restablecimiento de Contraseña"
    body = f"""
    Hola {nombre},
    
    Hemos recibido una solicitud para restablecer tu contraseña.
    
    Para continuar, haz clic en el siguiente enlace o copia y pégalo en tu navegador:
    http://localhost:8501/?reset_token={token}
    
    Este enlace expirará en 1 hora.
    
    Si no solicitaste restablecer tu contraseña, ignora este mensaje.
    
    Saludos,
    El equipo del sistema
    """
    
    try:
        if send_email(email, subject, body):
            return True, "Se ha enviado un enlace de restablecimiento a tu correo electrónico."
        else:
            return False, "Hubo un error al enviar el correo. Inténtalo de nuevo."
    except Exception as e:
        return False, f"Error al enviar el correo: {str(e)}"

def reset_password_with_token(token, new_password):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    
    c.execute("SELECT id, reset_token_expiration FROM users WHERE reset_token = ?", (token,))
    user = c.fetchone()
    
    if not user:
        conn.close()
        return False, "Token inválido o expirado."
    
    user_id, expiration_str = user
    
    try:
        expiration = datetime.fromisoformat(expiration_str)
    except ValueError:
        conn.close()
        return False, "Formato de token inválido."
    
    if datetime.now() > expiration:
        conn.close()
        return False, "Token expirado. Solicita un nuevo restablecimiento de contraseña."
    
    hashed_pw = hash_password(new_password)
    c.execute("UPDATE users SET password = ?, reset_token = NULL, reset_token_expiration = NULL WHERE id = ?", 
              (hashed_pw, user_id))
    conn.commit()
    conn.close()
    
    return True, "Contraseña restablecida exitosamente."