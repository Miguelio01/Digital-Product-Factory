import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from langchain_core.tools import tool

@tool
def send_email(to_email: str, subject: str, body: str, provider: str = 'gmail') -> str:
    """
    Envía un correo electrónico profesional.
    Provider: 'gmail' o 'outlook'.
    Requiere MAIL_USER y MAIL_PASS en el .env.
    """
    user = os.getenv('MAIL_USER')
    password = os.getenv('MAIL_PASS')
    
    if not user or not password: return 'Error: Credenciales de correo (MAIL_USER/MAIL_PASS) no configuradas.'

    try:
        # Configuración por proveedor
        if provider.lower() == 'gmail':
            smtp_server = 'smtp.gmail.com'
            port = 587
        elif provider.lower() == 'outlook':
            smtp_server = 'smtp.office365.com'
            port = 587
        else:
            return f'Error: Proveedor {provider} no soportado.'

        # Crear mensaje
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Enviar
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
        server.quit()

        return f'Correo enviado exitosamente a {to_email} vía {provider}.'
    except Exception as e: return f'Error enviando correo: {str(e)}'

MAIL_TOOLS = [send_email]
