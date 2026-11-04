import os
import smtplib
from email.message import EmailMessage

class EmailError(Exception):
    """Erro ao enviar e-mail"""

class EmailService:
    # SMTP do Mailtrap. No sandbox o e-mail fica no inbox do Mailtrap e não chega ao destinatário real
    @staticmethod
    def enviar(destino: str, assunto: str, texto: str, html: str | None = None) -> None:
        host = os.getenv("MAILTRAP_HOST")
        usuario = os.getenv("MAILTRAP_USER")
        senha = os.getenv("MAILTRAP_PASSWORD")
        if not (host and usuario and senha):
            raise EmailError("Credenciais do Mailtrap não estão configuradas no .env")

        msg = EmailMessage()
        msg["Subject"] = assunto
        msg["From"] = os.getenv("MAIL_FROM", "Estante Geek <nao-responda@estantegeek.local>")
        msg["To"] = destino
        msg.set_content(texto)
        if html:
            msg.add_alternative(html, subtype="html")

        try:
            with smtplib.SMTP(host, int(os.getenv("MAILTRAP_PORT", "2525")), timeout=10) as smtp:
                smtp.starttls()
                smtp.login(usuario, senha)
                smtp.send_message(msg)
        except (smtplib.SMTPException, OSError) as erro:
            raise EmailError(f"Falha ao enviar e-mail: {erro}") from erro