import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


SMTP_HOST     = 'sandbox.smtp.mailtrap.io'
SMTP_PORT     = 2525
SMTP_USER     = '5d2e5ad9511398'
SMTP_PASSWORD = '8e8dab69767ba5'
FROM_EMAIL    = 'noreply@alt-flotte.tn'
FROM_NAME     = 'ALT Fleet Management'


def send_email(to_email, subject, html_body):
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From']    = f'{FROM_NAME} <{FROM_EMAIL}>'
        msg['To']      = to_email
        msg.attach(MIMEText(html_body, 'html'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f'Email error: {e}')
        return False


def send_welcome_email(to_email, prenom, nom, temp_password):
    subject = 'Bienvenue sur ALT Fleet — Vos identifiants de connexion'
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background: #f4f6f9; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px;
                    padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #0d6efd;">AIR LIQUIDE TUNISIA</h2>
                <p style="color: #666; font-size: 13px;">Système de Gestion de Flotte</p>
            </div>
            <p>Bonjour <strong>{prenom} {nom}</strong>,</p>
            <p>Votre compte a été créé sur le système de gestion de flotte ALT.</p>
            <p>Voici vos identifiants de connexion :</p>
            <div style="background: #f8f9fc; border-radius: 8px; padding: 15px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Email :</strong> {to_email}</p>
                <p style="margin: 5px 0;"><strong>Mot de passe temporaire :</strong>
                    <span style="color: #dc3545; font-weight: bold; font-size: 18px;">
                        {temp_password}
                    </span>
                </p>
            </div>
            <p style="color: #dc3545; font-size: 13px;">
                ⚠️ Vous devrez changer votre mot de passe lors de votre première connexion.
            </p>
            <div style="text-align: center; margin-top: 25px;">
                <p style="color: #666; font-size: 12px;">
                    Ce message est automatique, merci de ne pas y répondre.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html)


def send_password_changed_email(to_email, prenom, nom):
    subject = 'ALT Fleet — Mot de passe modifié avec succès'
    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: Arial, sans-serif; background: #f4f6f9; padding: 20px;">
        <div style="max-width: 500px; margin: auto; background: white; border-radius: 10px;
                    padding: 30px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 20px;">
                <h2 style="color: #0d6efd;">AIR LIQUIDE TUNISIA</h2>
            </div>
            <p>Bonjour <strong>{prenom} {nom}</strong>,</p>
            <p>Votre mot de passe a été modifié avec succès.</p>
            <p style="color: #666; font-size: 13px;">
                Si vous n'êtes pas à l'origine de ce changement, contactez immédiatement votre administrateur.
            </p>
        </div>
    </body>
    </html>
    """
    return send_email(to_email, subject, html)