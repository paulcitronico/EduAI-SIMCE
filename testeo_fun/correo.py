import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# def las credendiales
remitente= 'jeanpachecotesista@gmail.com'
password = 'ecea gcpe ygqw nyal'  # Usa una contraseña de aplicación si usas 2FA

#destinatiario
input_email = input("Ingrese el correo del destinatario: ")
destinatario = input_email
asunto = 'Registro en plataforma'

# Cuerpo del mensaje
msj=MIMEMultipart()
msj['From']= remitente
msj['To']= destinatario
msj['Subject']= asunto

# Cuerpo del mensaje
cuerpo= 'Bienvenido registro exitoso'
msj.attach(MIMEText(cuerpo, 'plain'))

#inicar server smtp
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()  
server.login(remitente, password)

# Enviar el correo
texto = msj.as_string()
server.sendmail(remitente, destinatario, texto)
server.quit()
print("Correo enviado exitosamente")