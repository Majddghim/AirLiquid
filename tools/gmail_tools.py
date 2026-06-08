import os
import json
import base64
import time
import anthropic
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from requests_oauthlib import OAuth2Session


SCOPES              = ['https://www.googleapis.com/auth/gmail.readonly']
CREDENTIALS_FILE    = 'gmail_credentials.json'
TOKEN_FILE          = 'gmail_token.json'
REDIRECT_URI        = 'http://127.0.0.1:5000/gmail/callback'
GOOGLE_AUTH_URL     = 'https://accounts.google.com/o/oauth2/auth'
GOOGLE_TOKEN_URL    = 'https://oauth2.googleapis.com/token'


class GmailTools:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

    # ------------------------------------------------------------------ #
    # LOAD CLIENT SECRETS                                                  #
    # ------------------------------------------------------------------ #

    def load_client_secrets(self):
        with open(CREDENTIALS_FILE) as f:
            data = json.load(f)
        return data.get('web') or data.get('installed')

    # ------------------------------------------------------------------ #
    # AUTH URL                                                             #
    # ------------------------------------------------------------------ #

    def get_auth_url(self, redirect_uri=None):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        secrets   = self.load_client_secrets()
        client_id = secrets['client_id']

        oauth = OAuth2Session(client_id, scope=SCOPES, redirect_uri=REDIRECT_URI)
        auth_url, state = oauth.authorization_url(
            GOOGLE_AUTH_URL,
            access_type='offline',
            prompt='consent'
        )
        return auth_url, state

    # ------------------------------------------------------------------ #
    # EXCHANGE CODE FOR TOKEN                                              #
    # ------------------------------------------------------------------ #

    def exchange_code(self, code, redirect_uri=None):
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        secrets       = self.load_client_secrets()
        client_id     = secrets['client_id']
        client_secret = secrets['client_secret']

        oauth = OAuth2Session(client_id, redirect_uri=REDIRECT_URI, scope=SCOPES)

        token = oauth.fetch_token(
            GOOGLE_TOKEN_URL,
            code=code,
            client_secret=client_secret
        )

        with open(TOKEN_FILE, 'w') as f:
            json.dump(token, f)

        return True

    # ------------------------------------------------------------------ #
    # GET GMAIL SERVICE                                                    #
    # ------------------------------------------------------------------ #

    def get_service(self):
        if not os.path.exists(TOKEN_FILE):
            return None

        with open(TOKEN_FILE) as f:
            token = json.load(f)

        secrets       = self.load_client_secrets()
        client_id     = secrets['client_id']
        client_secret = secrets['client_secret']

        # refresh if expired
        try:
            expires_at = token.get('expires_at', 0)
            if time.time() > float(expires_at):
                oauth = OAuth2Session(client_id, token=token, redirect_uri=REDIRECT_URI)
                new_token = oauth.refresh_token(
                    GOOGLE_TOKEN_URL,
                    client_id=client_id,
                    client_secret=client_secret
                )
                with open(TOKEN_FILE, 'w') as f:
                    json.dump(new_token, f)
                token = new_token
        except Exception as e:
            print(f'Token refresh error: {e}')

        creds = Credentials(
            token=token.get('access_token'),
            refresh_token=token.get('refresh_token'),
            token_uri=GOOGLE_TOKEN_URL,
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES
        )

        return build('gmail', 'v1', credentials=creds)

    # ------------------------------------------------------------------ #
    # IS CONNECTED                                                         #
    # ------------------------------------------------------------------ #

    def is_connected(self):
        return os.path.exists(TOKEN_FILE)

    # ------------------------------------------------------------------ #
    # EXTRACT EMAIL BODY                                                   #
    # ------------------------------------------------------------------ #

    def get_email_body(self, message):
        body    = ''
        payload = message.get('payload', {})

        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                        break
                elif part.get('mimeType') == 'text/html' and not body:
                    data = part.get('body', {}).get('data', '')
                    if data:
                        body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
        else:
            data = payload.get('body', {}).get('data', '')
            if data:
                body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

        return body[:2000]

    # ------------------------------------------------------------------ #
    # IS FLEET RELATED                                                     #
    # ------------------------------------------------------------------ #

    def is_fleet_related(self, subject, body_preview):
        try:
            prompt = f"""Tu es un assistant qui analyse des emails pour une entreprise de gestion de flotte automobile (Air Liquide Tunisia).

Détermine si cet email est lié à la flotte de véhicules, aux voitures, à la maintenance, aux assurances, aux sinistres, aux carburants, aux garages, ou à tout sujet en rapport avec la gestion automobile.

Sujet: {subject}
Aperçu: {body_preview[:500]}

Réponds UNIQUEMENT avec: OUI ou NON"""

            response = self.client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=10,
                messages=[{'role': 'user', 'content': prompt}]
            )
            answer = response.content[0].text.strip().upper()
            return answer == 'OUI'
        except:
            return False

    # ------------------------------------------------------------------ #
    # FETCH FLEET EMAILS                                                   #
    # ------------------------------------------------------------------ #

    def fetch_fleet_emails(self, max_results=20):
        service = self.get_service()
        if not service:
            return []

        try:
            results = service.users().messages().list(
                userId='me',
                maxResults=max_results,
                labelIds=['INBOX']
            ).execute()

            messages     = results.get('messages', [])
            fleet_emails = []

            for msg in messages:
                full_msg = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()

                headers = {h['name']: h['value']
                           for h in full_msg.get('payload', {}).get('headers', [])}
                subject = headers.get('Subject', '(Sans objet)')
                sender  = headers.get('From', '')
                date    = headers.get('Date', '')
                msg_id  = full_msg['id']

                body = self.get_email_body(full_msg)

                if self.is_fleet_related(subject, body):
                    fleet_emails.append({
                        'id':      msg_id,
                        'subject': subject,
                        'sender':  sender,
                        'date':    date,
                        'preview': body[:200],
                        'body':    body
                    })

                if len(fleet_emails) >= 10:
                    break

            return fleet_emails

        except Exception as e:
            print(f'Gmail fetch error: {e}')
            return []

