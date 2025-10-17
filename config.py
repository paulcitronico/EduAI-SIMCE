import os

# Configuración de la aplicación
PAGE_TITLE = "Sistema de Login"
PAGE_LAYOUT = "wide"

# Configuración de correo
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "jeanpachecotesista@gmail.com"
SMTP_PASSWORD = "ecea gcpe ygqw nyal"

# Directorios
USER_IMAGES_DIR = "user_images"
ARCHIVOS_PROFESORES_DIR = "archivos_profesores"
TEMP_CONVERSION_DIR = "temp_conversion"
VIDEOS_TUTORIALES_DIR = "videos_tutoriales"

# Crear directorios si no existen
for directory in [USER_IMAGES_DIR, ARCHIVOS_PROFESORES_DIR, TEMP_CONVERSION_DIR, VIDEOS_TUTORIALES_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)