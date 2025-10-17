import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import config

def send_email(to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = config.SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT)
        server.starttls()
        server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(config.SMTP_USERNAME, to_email, text)
        server.quit()
        return True
    except Exception as e:
        print(f"Error al enviar el correo: {str(e)}")
        return False

def show_all_emails():
    import sqlite3
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT email FROM users")
    emails = c.fetchall()
    conn.close()
    return [email[0] for email in emails]