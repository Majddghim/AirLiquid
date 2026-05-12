import anthropic
import base64
import os
import json


class OCRTools:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        self.model  = 'claude-haiku-4-5-20251001'

    # ------------------------------------------------------------------ #
    # INTERNAL                                                             #
    # ------------------------------------------------------------------ #

    def _encode_file(self, file_path):
        """Encode file to base64"""
        with open(file_path, 'rb') as f:
            return base64.standard_b64encode(f.read()).decode('utf-8')

    def _get_media_type(self, file_path):
        ext = file_path.lower().split('.')[-1]
        return {
            'jpg':  'image/jpeg',
            'jpeg': 'image/jpeg',
            'png':  'image/png',
            'pdf':  'application/pdf',
            'webp': 'image/webp'
        }.get(ext, 'image/jpeg')

    def _call_claude(self, file_path, prompt):
        """Send file to Claude and get structured JSON response"""
        try:
            media_type  = self._get_media_type(file_path)
            file_data   = self._encode_file(file_path)
            is_pdf      = media_type == 'application/pdf'

            if is_pdf:
                content = [
                    {
                        'type': 'document',
                        'source': {
                            'type':       'base64',
                            'media_type': 'application/pdf',
                            'data':       file_data
                        }
                    },
                    {'type': 'text', 'text': prompt}
                ]
            else:
                content = [
                    {
                        'type': 'image',
                        'source': {
                            'type':       'base64',
                            'media_type': media_type,
                            'data':       file_data
                        }
                    },
                    {'type': 'text', 'text': prompt}
                ]

            response = self.client.messages.create(
                model      = self.model,
                max_tokens = 1000,
                messages   = [{'role': 'user', 'content': content}]
            )

            raw = response.content[0].text.strip()
            # clean markdown code blocks if present
            if raw.startswith('```'):
                raw = raw.split('```')[1]
                if raw.startswith('json'):
                    raw = raw[4:]
            return json.loads(raw.strip())

        except Exception as e:
            print(f'OCR error: {e}')
            return None

    # ------------------------------------------------------------------ #
    # DOCUMENT SCAN METHODS                                                #
    # ------------------------------------------------------------------ #

    def scan_carte_grise(self, file_path):
        prompt = """Tu es un assistant OCR spécialisé dans les cartes grises tunisiennes.
Extrais les informations suivantes de ce document et retourne UNIQUEMENT un JSON valide, sans explication.

Champs à extraire:
- model: modèle commercial du véhicule UNIQUEMENT (Type commercial) — ex: FLUENCE, CLIO, 208, PARTNER. NE PAS mettre la marque ici.
- brand: marque du constructeur UNIQUEMENT (Constructeur) — ex: RENAULT, PEUGEOT, TOYOTA. NE PAS mettre le modèle ici.
- year: année de première circulation (nombre entier extrait de la date DPMC)
- plate_number: numéro d'immatriculation visible verticalement sur le côté GAUCHE. Convertis le format arabe en format latin: ex "159 تونس 8085" devient "159 TU 8085"
- owner_name: nom et prénom complet du propriétaire (Nom et Prénom)
- chassis_number: numéro de châssis VIN complet (N° Serie du type)
- puissance_fiscale: null si non visible
- carburant: null si non visible
- registration_date: date DPMC au format YYYY-MM-DD
- expiration_date: null si non visible

Règle importante: 
- brand = RENAULT, PEUGEOT, TOYOTA etc (le constructeur)
- model = FLUENCE, CLIO, 208 etc (le type commercial)
Ces deux champs sont TOUJOURS différents.

Retourne UNIQUEMENT le JSON, rien d'autre."""
        return self._call_claude(file_path, prompt)

    def scan_assurance(self, file_path):
        prompt = """Tu es un assistant OCR spécialisé dans les attestations d'assurance tunisiennes.
Extrais les informations suivantes et retourne UNIQUEMENT un JSON valide, sans explication.

Champs à extraire:
- insurer: nom de la compagnie d'assurance (Entreprise d'Assurance / مؤسسة التأمين) — ex: MAE, STAR, COMAR
- policy_number: numéro de contrat (Contrat N°) — ex: 10/100155152
- start_date: date de DÉBUT de validité (Validité Du / الصلوحية من) au format YYYY-MM-DD
- end_date: date de FIN de validité (Validité Au / إلى) au format YYYY-MM-DD

Règle importante pour les dates:
- La date Du (début) est TOUJOURS avant la date Au (fin)
- start_date DOIT être antérieure à end_date
- Les dates sont au format JJ/MM/AAAA dans le document

Si un champ n'est pas trouvé, mettre null.
Retourne UNIQUEMENT le JSON, rien d'autre."""
        return self._call_claude(file_path, prompt)

    def scan_vignette(self, file_path):
        prompt = """Tu es un assistant OCR spécialisé dans les vignettes automobiles tunisiennes.
Extrais les informations suivantes et retourne UNIQUEMENT un JSON valide, sans explication.

Champs à extraire:
- year: année de la vignette (nombre entier)
- montant: montant payé (nombre décimal)
- expiration_date: date d'expiration (format YYYY-MM-DD)

Si un champ n'est pas trouvé, mettre null.
Retourne UNIQUEMENT le JSON, rien d'autre."""
        return self._call_claude(file_path, prompt)

    def scan_visite_technique(self, file_path):
        prompt = """Tu es un assistant OCR spécialisé dans les certificats de visite technique tunisiens.
Extrais les informations suivantes et retourne UNIQUEMENT un JSON valide, sans explication.

Champs à extraire:
- expiration_date: date d'expiration au format YYYY-MM-DD
- montant: montant payé en DT si visible, sinon null

Règles IMPORTANTES pour trouver la bonne date d'expiration:
- Le document contient DEUX dates
- La première date est تاريخ التسليم (date de délivrance) — NE PAS utiliser cette date
- La deuxième date est صالحة إلى غاية (valide jusqu'à) — C'EST CETTE DATE QU'ON VEUT
- La date صالحة إلى غاية est TOUJOURS plus récente (année plus grande) que تاريخ التسليم
- Dans ce document: صالحة إلى غاية = 2026/07/08 → retourner 2026-07-08
- Format dans le document: AAAA/MM/JJ → convertir en YYYY-MM-DD

Retourne UNIQUEMENT le JSON, rien d'autre."""
        return self._call_claude(file_path, prompt)

    def scan_facture(self, file_path):
        prompt = """Tu es un assistant OCR spécialisé dans les factures tunisiennes.
Extrais les informations suivantes et retourne UNIQUEMENT un JSON valide, sans explication.

Champs à extraire:
- num_facture: numéro de facture
- date_facture: date de la facture (format YYYY-MM-DD)
- montant_ht: montant hors taxes (nombre décimal)
- tva: montant TVA (nombre décimal)
- montant_ttc: montant toutes taxes comprises (nombre décimal)
- num_reglement: numéro de règlement/chèque/virement si présent

Si un champ n'est pas trouvé, mettre null.
Retourne UNIQUEMENT le JSON, rien d'autre."""
        return self._call_claude(file_path, prompt)

    def scan_constat(self, file_path):
        prompt = """Tu es un assistant OCR spécialisé dans les constats d'accident tunisiens.
Extrais les informations suivantes et retourne UNIQUEMENT un JSON valide, sans explication.

Champs à extraire:
- n_constat: numéro du constat
- date_constat: date du constat (format YYYY-MM-DD)
- description: description de l'accident/sinistre

Si un champ n'est pas trouvé, mettre null.
Retourne UNIQUEMENT le JSON, rien d'autre."""
        return self._call_claude(file_path, prompt)

    def scan_odometer(self, file_path):
        prompt = """Tu es un assistant OCR. Lis le nombre affiché dans cette image.
Il peut s'agir d'un compteur kilométrique, un écran numérique, ou tout affichage de chiffres.

Retourne UNIQUEMENT un JSON valide:
- km: le nombre entier que tu vois (sans espaces ni points ni virgules), ex: 47500
- confidence: "high", "medium", ou "low"

Si l'image est floue ou illisible, essaie quand même de donner une estimation.
Si vraiment impossible, retourne {"km": null, "confidence": "low"}
Retourne UNIQUEMENT le JSON, rien d'autre."""
        return self._call_claude(file_path, prompt)

    def analyze_car_damage(self, file_path):
        prompt = """Tu es un expert en évaluation de dommages automobiles.
    Analyse cette photo d'un véhicule et décris les dommages visibles.

    Retourne UNIQUEMENT un JSON valide:
    - description: description courte des dommages en français (2-3 phrases max)
    - severity: "léger", "modéré", ou "grave"
    - parts_affected: liste des parties endommagées (ex: ["pare-choc avant", "phare gauche"])

    Si aucun dommage visible, retourne {"description": "Aucun dommage visible", "severity": "aucun", "parts_affected": []}
    Retourne UNIQUEMENT le JSON, rien d'autre."""
        return self._call_claude(file_path, prompt)