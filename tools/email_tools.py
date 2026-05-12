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

def send_weekly_digest(to_email, data):
    """Send weekly fleet digest email to RH"""
    today    = __import__('datetime').date.today()
    subject  = f"ALT Fleet — Résumé hebdomadaire du {today.strftime('%d/%m/%Y')}"

    fleet    = data.get('fleet', {})
    expenses = data.get('expenses', {})
    alerts   = data.get('alerts', [])[:3]
    anomalies = data.get('anomalies', [])[:3]

    # fleet status row
    def kpi_box(label, value, color):
        return f"""
        <td style="text-align:center;padding:15px;">
            <div style="font-size:28px;font-weight:bold;color:{color};">{value}</div>
            <div style="font-size:11px;color:#666;margin-top:4px;">{label}</div>
        </td>"""

    fleet_row = f"""
    <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            {kpi_box('Total véhicules', fleet.get('total', 0), '#0d6efd')}
            {kpi_box('Opérationnels', fleet.get('active', 0), '#198754')}
            {kpi_box('En maintenance', fleet.get('maintenance', 0), '#ffc107')}
            {kpi_box('Dossiers incomplets', fleet.get('incomplete', 0), '#dc3545')}
        </tr>
    </table>"""

    # expense row
    expense_row = f"""
    <table width="100%" cellpadding="0" cellspacing="0">
        <tr>
            {kpi_box('Maintenance', f"{expenses.get('maintenance', 0):,.0f} DT", '#0d6efd')}
            {kpi_box('Sinistres', f"{expenses.get('sinistres', 0):,.0f} DT", '#dc3545')}
            {kpi_box('Carburant', f"{expenses.get('carburant', 0):,.0f} DT", '#ffc107')}
            {kpi_box('Total', f"{expenses.get('total', 0):,.0f} DT", '#198754')}
        </tr>
    </table>"""

    # alerts list
    alerts_html = ''
    if alerts:
        for a in alerts:
            color = '#dc3545' if a.get('level') == 'danger' else '#ffc107'
            alerts_html += f"""
            <tr>
                <td style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
                    <span style="color:{color};font-weight:bold;">⚠</span>
                    {a.get('doc', '')} — {a.get('car', '')}
                </td>
                <td style="padding:8px 0;border-bottom:1px solid #f0f0f0;
                    text-align:right;color:#666;font-size:12px;">
                    {f"dans {a.get('days')} jours" if a.get('days') else 'Expiré'}
                </td>
            </tr>"""
    else:
        alerts_html = '<tr><td colspan="2" style="color:#198754;padding:8px 0;">✅ Aucune alerte active</td></tr>'

    # anomalies list
    anomalies_html = ''
    if anomalies:
        for an in anomalies:
            anomalies_html += f"""
            <tr>
                <td style="padding:8px 0;border-bottom:1px solid #f0f0f0;">
                    🚨 {an.get('model') or an.get('brand', '')} —
                    {an.get('plate_number', '')}
                </td>
                <td style="padding:8px 0;border-bottom:1px solid #f0f0f0;
                    text-align:right;color:#dc3545;font-weight:bold;">
                    {an.get('ratio', '')}x la moyenne
                </td>
            </tr>"""
    else:
        anomalies_html = '<tr><td colspan="2" style="color:#198754;padding:8px 0;">✅ Aucune anomalie détectée</td></tr>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family:Arial,sans-serif;background:#f4f6f9;padding:20px;margin:0;">
        <div style="max-width:600px;margin:auto;background:white;border-radius:12px;
                    overflow:hidden;box-shadow:0 4px 20px rgba(0,0,0,0.1);">

            <!-- Header -->
            <div style="background:linear-gradient(135deg,#0d6efd,#0056d3);
                        padding:30px;text-align:center;">
                <h1 style="color:white;margin:0;font-size:22px;">
                    AIR LIQUIDE TUNISIA
                </h1>
                <p style="color:rgba(255,255,255,0.8);margin:5px 0 0;font-size:13px;">
                    Résumé hebdomadaire de la flotte — {today.strftime('%d/%m/%Y')}
                </p>
            </div>

            <!-- Fleet KPIs -->
            <div style="padding:20px 25px 0;">
                <h3 style="color:#0d6efd;font-size:13px;text-transform:uppercase;
                           letter-spacing:1px;margin:0 0 15px;">
                    État de la flotte
                </h3>
                <div style="background:#f8f9fc;border-radius:10px;padding:10px;">
                    {fleet_row}
                </div>
            </div>

            <!-- Expenses -->
            <div style="padding:20px 25px 0;">
                <h3 style="color:#0d6efd;font-size:13px;text-transform:uppercase;
                           letter-spacing:1px;margin:0 0 15px;">
                    Dépenses — {['Janvier','Février','Mars','Avril','Mai','Juin','Juillet','Août','Septembre','Octobre','Novembre','Décembre'][today.month-1] + ' ' + str(today.year)}
                </h3>
                <div style="background:#f8f9fc;border-radius:10px;padding:10px;">
                    {expense_row}
                </div>
            </div>

            <!-- Alerts -->
            <div style="padding:20px 25px 0;">
                <h3 style="color:#ffc107;font-size:13px;text-transform:uppercase;
                           letter-spacing:1px;margin:0 0 15px;">
                    ⚠️ Top 3 Alertes urgentes
                </h3>
                <table width="100%" cellpadding="0" cellspacing="0">
                    {alerts_html}
                </table>
            </div>

            <!-- Anomalies -->
            <div style="padding:20px 25px 0;">
                <h3 style="color:#dc3545;font-size:13px;text-transform:uppercase;
                           letter-spacing:1px;margin:0 0 15px;">
                    🚨 Anomalies de dépenses détectées
                </h3>
                <table width="100%" cellpadding="0" cellspacing="0">
                    {anomalies_html}
                </table>
            </div>

            <!-- Footer -->
            <div style="padding:25px;margin-top:20px;text-align:center;
                        background:#f8f9fc;border-top:1px solid #dee2e6;">
                <p style="color:#666;font-size:12px;margin:0;">
                    Ce rapport est généré automatiquement chaque lundi à 8h00.
                </p>
                <p style="color:#aaa;font-size:11px;margin:5px 0 0;">
                    ALT Fleet Management — Air Liquide Tunisia
                </p>
            </div>

        </div>
    </body>
    </html>"""

    return send_email(to_email, subject, html)