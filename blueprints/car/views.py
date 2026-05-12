import time
import os
from services.voiture import VoitureService
from services.employe import EmployeService
from flask import Blueprint, request, jsonify, render_template
from werkzeug.utils import secure_filename
from tools.ocr_tools import OCRTools


class CarViews:
    def __init__(self):
        self.VoitureService = VoitureService()
        self.EmployeService = EmployeService()
        self.car_bp = Blueprint('car', __name__)
        self.car_routes()

    def car_routes(self):

        # ------------------------------------------------------------------ #
        # EXISTING ROUTES                                                      #
        # ------------------------------------------------------------------ #

        @self.car_bp.route('/ajout-voiture', methods=['POST'])
        def ajout_voiture():
            model            = request.form.get('model')
            year             = request.form.get('year')
            plate_number     = request.form.get('plate_number')
            owner_name       = request.form.get('owner_name')
            chassis_number   = request.form.get('chassis_number')
            status           = request.form.get('status')
            acquisition_date = request.form.get('acquisition_date')
            registration_date= request.form.get('registration_date')
            expiration_date  = request.form.get('expiration_date')
            notes            = request.form.get('notes')

            file_path = None
            if 'carte_grise' in request.files:
                file = request.files['carte_grise']
                if file.filename != '':
                    upload_folder = 'static/uploads/carte_grises'
                    os.makedirs(upload_folder, exist_ok=True)
                    filename  = secure_filename(f"{plate_number}_{file.filename}")
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)

            if not model or not year or not plate_number or not status:
                return jsonify({'status': 'failed', 'message': 'Veuillez remplir les champs obligatoires'})

            try:
                voiture_id = self.VoitureService.ajouter_voiture(
                    model=model, year=year, plate_number=plate_number,
                    owner_name=owner_name, chassis_number=chassis_number,
                    status=status, registration_date=registration_date,
                    expiration_date=expiration_date, acquisition_date=acquisition_date,
                    notes=notes, file_path=file_path
                )
                return jsonify({'status': 'success', 'message': 'Voiture ajoutée avec succès', 'voiture_id': voiture_id})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)})

        @self.car_bp.route('/extract-data', methods=['POST'])
        def extract_data():
            if 'file' not in request.files:
                return jsonify({'status': 'failed', 'message': 'Pas de fichier document trouvé'})
            file = request.files['file']
            if file.filename == '':
                return jsonify({'status': 'failed', 'message': 'Le fichier est vide'})
            mock_data = {
                "model": "Peugeot Partner", "year": "2021",
                "plate_number": f"TEST TU {int(time.time()) % 10000}",
                "owner_name": "AIR LIQUID S.A",
                "chassis_number": f"VN7890BC{int(time.time()) % 100000}",
                "puissance_fiscale": "7", "carburant": "diesel",
                "registration_date": "2021-03-20", "expiration_date": "2025-03-20"
            }
            time.sleep(1.5)
            return jsonify({'status': 'success', 'extracted_data': mock_data})

        @self.car_bp.route('/get-voitures', methods=['GET'])
        def get_voitures():
            search_by_name = request.args.get('search_by_name', '').strip()
            page  = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 10, type=int)
            try:
                offset = (page - 1) * limit
                voitures, total_count = self.VoitureService.get_voitures_paginated(
                    search_by_name=search_by_name, limit=limit, offset=offset)
                return jsonify({'status': 'success', 'data': voitures, 'count': total_count})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.car_bp.route('/get-all-voitures', methods=['GET'])
        def get_all_voitures():
            try:
                voitures = self.VoitureService.get_all_voitures()
                return jsonify({'status': 'success', 'data': voitures})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.car_bp.route('/get-voiture/<int:car_id>', methods=['GET'])
        def get_voiture(car_id):
            try:
                voiture = self.VoitureService.get_voiture_by_id(car_id)
                if not voiture:
                    return jsonify({'status': 'failed', 'message': 'Voiture introuvable'}), 404
                return jsonify({'status': 'success', 'data': voiture})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # ------------------------------------------------------------------ #
        # CAR DETAIL PAGE                                                      #
        # ------------------------------------------------------------------ #

        @self.car_bp.route('/detail/<int:car_id>', methods=['GET'])
        def detail(car_id):
            return render_template('car-detail.html')

        @self.car_bp.route('/detail-data/<int:car_id>', methods=['GET'])
        def detail_data(car_id):
            try:
                data = self.VoitureService.get_car_detail(car_id)
                if not data:
                    return jsonify({'status': 'failed', 'message': 'Voiture introuvable'}), 404
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # ------------------------------------------------------------------ #
        # SCAN FLOW                                                            #
        # ------------------------------------------------------------------ #

        @self.car_bp.route('/upload-cg', methods=['POST'])
        def upload_cg():
            if 'file' not in request.files:
                return jsonify({'status': 'failed', 'message': 'Aucun fichier reçu'})
            file = request.files['file']
            if file.filename == '':
                return jsonify({'status': 'failed', 'message': 'Fichier vide'})
            try:
                upload_folder = 'static/uploads/carte_grises'
                os.makedirs(upload_folder, exist_ok=True)
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                # real OCR
                ocr = OCRTools()
                extracted_data = ocr.scan_carte_grise(file_path)

                if not extracted_data:
                    return jsonify({'status': 'failed', 'message': 'Impossible d\'extraire les données du document'})

                cg_id = self.VoitureService.save_temp_carte_grise(file_path, extracted_data)
                return jsonify({
                    'status': 'success',
                    'cg_id': cg_id,
                    'extracted_data': extracted_data,
                    'file_path': file_path
                })
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)})

        @self.car_bp.route('/confirm/<int:cg_id>', methods=['POST'])
        def confirm_car(cg_id):
            try:
                form_data = {
                    'plate_number':     request.form.get('plate_number'),
                    'brand':            request.form.get('brand'),
                    'model':            request.form.get('model'),
                    'status':           request.form.get('status', 'active'),
                    'acquisition_date': request.form.get('acquisition_date'),
                    'notes':            request.form.get('notes'),
                    'year':             request.form.get('year'),
                    'owner_name':       request.form.get('owner_name'),
                    'chassis_number':   request.form.get('chassis_number'),
                    'puissance_fiscale':request.form.get('puissance_fiscale'),
                    'carburant':        request.form.get('carburant'),
                    'registration_date':request.form.get('registration_date'),
                    'expiration_date':  request.form.get('expiration_date'),
                }
                car_id = self.VoitureService.confirm_car_creation(cg_id, form_data)
                return jsonify({
                    'status': 'success', 'message': 'Voiture créée avec succès',
                    'car_id': car_id,
                    'redirect': f'/car/dossier?car_id={car_id}'
                })
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)})

        # ------------------------------------------------------------------ #
        # DOSSIER PAGE                                                         #
        # ------------------------------------------------------------------ #

        @self.car_bp.route('/dossier', methods=['GET'])
        def dossier():
            return render_template('car-dossier.html')

        # ------------------------------------------------------------------ #
        # DOCUMENT SCAN + SAVE                                                 #
        # ------------------------------------------------------------------ #

        @self.car_bp.route('/scan-document/<int:car_id>', methods=['POST'])
        def scan_document(car_id):
            doc_type = request.form.get('doc_type')
            if 'file' not in request.files:
                return jsonify({'status': 'failed', 'message': 'Aucun fichier reçu'})
            file = request.files['file']
            if file.filename == '':
                return jsonify({'status': 'failed', 'message': 'Fichier vide'})

            try:
                upload_folder = f'static/uploads/{doc_type}'
                os.makedirs(upload_folder, exist_ok=True)
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                ocr = OCRTools()
                mock = None

                if doc_type == 'assurance':
                    mock = ocr.scan_assurance(file_path)
                elif doc_type == 'vignette':
                    mock = ocr.scan_vignette(file_path)
                elif doc_type == 'visite':
                    mock = ocr.scan_visite_technique(file_path)
                elif doc_type == 'facture':
                    mock = ocr.scan_facture(file_path)
                else:
                    return jsonify({'status': 'failed', 'message': 'Type de document inconnu'})

                if not mock:
                    return jsonify({'status': 'failed', 'message': 'Impossible d\'extraire les données'})

                return jsonify({'status': 'success', 'extracted_data': mock, 'file_path': file_path})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)})

        @self.car_bp.route('/save-document/<int:car_id>/<doc_type>', methods=['POST'])
        def save_document(car_id, doc_type):
            try:
                file_path = None
                if 'file' in request.files:
                    file = request.files['file']
                    if file and file.filename != '':
                        upload_folder = f'static/uploads/{doc_type}'
                        os.makedirs(upload_folder, exist_ok=True)
                        filename  = secure_filename(file.filename)
                        file_path = os.path.join(upload_folder, filename)
                        file.save(file_path)

                if doc_type == 'assurance':
                    self.VoitureService.save_assurance(
                        car_id=car_id,
                        insurer=request.form.get('insurer'),
                        policy_number=request.form.get('policy_number'),
                        start_date=request.form.get('start_date'),
                        end_date=request.form.get('end_date'),
                        file_path=file_path
                    )
                elif doc_type == 'vignette':
                    self.VoitureService.save_vignette(
                        car_id=car_id,
                        year=request.form.get('year'),
                        expiration_date=request.form.get('expiration_date'),
                        montant=request.form.get('montant'),
                        file_path=file_path
                    )
                elif doc_type == 'visite':
                    self.VoitureService.save_visite_technique(
                        car_id=car_id,
                        expiration_date=request.form.get('expiration_date'),
                        montant=request.form.get('montant'),
                        file_path=file_path
                    )
                else:
                    return jsonify({'status': 'failed', 'message': 'Type de document inconnu'})

                return jsonify({'status': 'success', 'message': 'Document enregistré avec succès'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)})

        # ------------------------------------------------------------------ #
        # AFFECTATION                                                          #
        # ------------------------------------------------------------------ #

        @self.car_bp.route('/get-employes-list', methods=['GET'])
        def get_employes_list():
            try:
                employes = self.EmployeService.get_all_employes()
                actifs = [e for e in employes if e.get('status') == 'active']
                return jsonify({'status': 'success', 'data': actifs})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.car_bp.route('/get-affectation/<int:car_id>', methods=['GET'])
        def get_affectation(car_id):
            try:
                affectation = self.VoitureService.get_affectation_active(car_id)
                if affectation:
                    return jsonify({'status': 'success', 'assigned': True, 'data': affectation})
                return jsonify({'status': 'success', 'assigned': False})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.car_bp.route('/affecter/<int:car_id>', methods=['POST'])
        def affecter_voiture(car_id):
            try:
                employee_id = request.form.get('employee_id')
                start_date  = request.form.get('start_date')
                notes       = request.form.get('notes') or None
                admin_id    = 1

                if not employee_id or not start_date:
                    return jsonify({'status': 'failed', 'message': 'Employé et date de début sont obligatoires'})

                self.VoitureService.affecter_voiture(
                    car_id=car_id, employee_id=int(employee_id),
                    start_date=start_date, admin_id=admin_id, notes=notes
                )
                return jsonify({'status': 'success', 'message': 'Véhicule affecté avec succès'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)})

        # ------------------------------------------------------------------ #
        # BRANDS & MODELS                                                      #
        # ------------------------------------------------------------------ #

        @self.car_bp.route('/get-brands', methods=['GET'])
        def get_brands():
            try:
                brands = self.VoitureService.get_brands()
                return jsonify({'status': 'success', 'data': brands})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.car_bp.route('/get-models/<int:brand_id>', methods=['GET'])
        def get_models(brand_id):
            try:
                models = self.VoitureService.get_models_by_brand(brand_id)
                return jsonify({'status': 'success', 'data': models})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.car_bp.route('/update/<int:car_id>', methods=['PUT'])
        def update_voiture(car_id):
            try:
                data = request.get_json()
                self.VoitureService.update_voiture(
                    car_id=car_id,
                    brand=data.get('brand', '').strip(),
                    model=data.get('model', '').strip(),
                    plate_number=data.get('plate_number', '').strip(),
                    year=data.get('year'),
                    owner_name=data.get('owner_name'),
                    chassis_number=data.get('chassis_number'),
                    puissance_fiscale=data.get('puissance_fiscale'),
                    carburant=data.get('carburant'),
                    registration_date=data.get('registration_date') or None,
                    expiration_date=data.get('expiration_date') or None,
                    acquisition_date=data.get('acquisition_date') or None,
                    status=data.get('status', 'active'),
                    notes=data.get('notes')
                )
                return jsonify({'status': 'success', 'message': 'Véhicule mis à jour avec succès'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.car_bp.route('/delete/<int:car_id>', methods=['DELETE'])
        def delete_voiture(car_id):
            try:
                self.VoitureService.supprimer_voiture(car_id)
                return jsonify({'status': 'success', 'message': 'Véhicule retiré avec succès'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.car_bp.route('/historique/<int:car_id>', methods=['GET'])
        def historique(car_id):
            return render_template('car-historique.html')

        @self.car_bp.route('/export-dossier/<int:car_id>', methods=['GET'])
        def export_dossier(car_id):
            try:
                from reportlab.lib.pagesizes import A4
                from reportlab.lib import colors
                from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
                from reportlab.lib.units import cm
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
                from reportlab.lib.enums import TA_CENTER, TA_LEFT
                from io import BytesIO
                import datetime

                # fetch all data
                from services.maintenance import MaintenanceService
                from services.sinistre import SinistreService

                car_data = self.VoitureService.get_car_detail(car_id)
                if not car_data:
                    return jsonify({'status': 'failed', 'message': 'Voiture introuvable'}), 404

                maint_service = MaintenanceService()
                sin_service = SinistreService()

                records = maint_service.get_records_by_car(car_id)
                alerts = maint_service.get_alerts_by_car(car_id)
                sinistres = sin_service.get_sinistres_by_car(car_id)
                km_data = maint_service.get_current_km(car_id)

                car = car_data['car']
                docs = car_data['documents']

                buffer = BytesIO()
                doc = SimpleDocTemplate(
                    buffer, pagesize=A4,
                    rightMargin=1.5 * cm, leftMargin=1.5 * cm,
                    topMargin=1.5 * cm, bottomMargin=1.5 * cm
                )

                styles = getSampleStyleSheet()
                elements = []

                # colors
                BLUE = colors.HexColor('#0d6efd')
                GRAY = colors.HexColor('#6c757d')
                LIGHT = colors.HexColor('#f8f9fc')
                DARK = colors.HexColor('#2d3748')
                GREEN = colors.HexColor('#198754')
                RED = colors.HexColor('#dc3545')
                YELLOW = colors.HexColor('#ffc107')

                title_style = ParagraphStyle('T', parent=styles['Title'],
                                             fontSize=20, textColor=BLUE, alignment=TA_CENTER, spaceAfter=2)
                sub_style = ParagraphStyle('S', parent=styles['Normal'],
                                           fontSize=9, textColor=GRAY, alignment=TA_CENTER, spaceAfter=4)
                section_style = ParagraphStyle('SEC', parent=styles['Heading2'],
                                               fontSize=11, textColor=BLUE, spaceBefore=12, spaceAfter=6)
                normal_style = ParagraphStyle('N', parent=styles['Normal'],
                                              fontSize=9, textColor=DARK)

                def section_title(text, icon=''):
                    elements.append(Spacer(1, 0.3 * cm))
                    elements.append(HRFlowable(width='100%', thickness=1, color=BLUE))
                    elements.append(Paragraph(f"{icon} {text}", section_style))

                def info_table(data):
                    t = Table(data, colWidths=[5 * cm, 11 * cm])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), LIGHT),
                        ('TEXTCOLOR', (0, 0), (0, -1), GRAY),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('TEXTCOLOR', (1, 0), (1, -1), DARK),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                        ('ROWHEIGHT', (0, 0), (-1, -1), 18),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ]))
                    elements.append(t)

                # ---- HEADER ----
                elements.append(Paragraph('AIR LIQUIDE TUNISIA', title_style))
                elements.append(Paragraph('Système de Gestion de Flotte', sub_style))
                elements.append(Paragraph('DOSSIER VÉHICULE', ParagraphStyle('DV',
                                                                             parent=styles['Heading1'], fontSize=16,
                                                                             textColor=DARK,
                                                                             alignment=TA_CENTER, spaceAfter=2)))
                elements.append(Paragraph(
                    f"Généré le {datetime.date.today().strftime('%d/%m/%Y')}",
                    sub_style))
                elements.append(HRFlowable(width='100%', thickness=3, color=BLUE))

                # ---- CARTE GRISE ----
                section_title('Carte Grise & Identification', '🚗')
                info_table([
                    ['Immatriculation', car.get('plate_number') or '—'],
                    ['Marque', car.get('brand') or '—'],
                    ['Modèle', car.get('model') or '—'],
                    ['Année', str(car.get('year') or '—')],
                    ['Propriétaire', car.get('owner_name') or '—'],
                    ['Châssis (VIN)', car.get('chassis_number') or '—'],
                    ['Carburant', car.get('carburant') or '—'],
                    ['Puissance', f"{car.get('puissance_fiscale') or '—'} CV"],
                    ['Statut', car.get('status') or '—'],
                    ['Date acquisition', str(car.get('acquisition_date') or '—')],
                ])

                # ---- KM ----
                section_title('Kilométrage', '📍')
                if km_data:
                    info_table([
                        ['KM actuel', f"{int(km_data['km']):,} km".replace(',', ' ')],
                        ['Relevé le', str(km_data['recorded_at'])],
                    ])
                else:
                    elements.append(Paragraph('Aucun relevé kilométrique enregistré.', normal_style))

                # ---- DOCUMENTS ----
                section_title('Documents', '📄')
                ass = docs.get('assurance')
                vig = docs.get('vignette')
                vt = docs.get('visite')

                doc_data = [['Document', 'Statut', 'Détails', 'Expiration']]
                doc_data.append([
                    'Assurance',
                    'Valide' if ass and not ass.get('expired') else ('Expiré' if ass else 'Manquant'),
                    ass.get('insurer', '—') if ass else '—',
                    str(ass.get('end_date', '—')) if ass else '—'
                ])
                doc_data.append([
                    'Vignette',
                    'Valide' if vig else 'Manquant',
                    str(vig.get('year', '—')) if vig else '—',
                    str(vig.get('expiration_date', '—')) if vig else '—'
                ])
                doc_data.append([
                    'Visite Technique',
                    'Valide' if vt else 'Manquant',
                    '—',
                    str(vt.get('expiration_date', '—')) if vt else '—'
                ])

                doc_table = Table(doc_data, colWidths=[4 * cm, 3 * cm, 5 * cm, 4 * cm])
                doc_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), BLUE),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
                    ('ROWHEIGHT', (0, 0), (-1, -1), 18),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]))
                elements.append(doc_table)

                # ---- AFFECTATION ----
                section_title('Affectation', '👤')
                aff = car_data.get('affectation')
                if aff:
                    info_table([
                        ['Employé', f"{aff.get('prenom', '')} {aff.get('nom', '')}"],
                        ['Poste', aff.get('poste') or '—'],
                        ['Département', aff.get('departement') or '—'],
                        ['Depuis', str(aff.get('start_date') or '—')],
                    ])
                else:
                    elements.append(Paragraph('Aucun employé affecté.', normal_style))

                # ---- MAINTENANCE ALERTS ----
                section_title('Alertes Maintenance', '🔧')
                if alerts:
                    alert_data = [['Pièce', 'Type', 'Échéance Date', 'Échéance KM']]
                    for a in alerts[:10]:
                        alert_data.append([
                            a.get('part_name', '—'),
                            a.get('alert_type', '—'),
                            str(a.get('due_date') or '—'),
                            str(a.get('due_km') or '—'),
                        ])
                    at = Table(alert_data, colWidths=[5 * cm, 3 * cm, 4 * cm, 4 * cm])
                    at.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), YELLOW),
                        ('TEXTCOLOR', (0, 0), (-1, 0), DARK),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
                        ('ROWHEIGHT', (0, 0), (-1, -1), 18),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ]))
                    elements.append(at)
                else:
                    elements.append(Paragraph('Aucune alerte maintenance active.', normal_style))

                # ---- MAINTENANCE HISTORY ----
                section_title('Historique des Entretiens', '📋')
                if records:
                    rec_data = [['Pièce', 'Garage', 'Date', 'KM', 'Montant']]
                    for r in records[:10]:
                        rec_data.append([
                            r.get('part_name', '—'),
                            r.get('garage_name') or '—',
                            str(r.get('done_at') or '—'),
                            str(r.get('km_at_service') or '—'),
                            f"{r.get('montant_ttc') or '—'} DT",
                        ])
                    rt = Table(rec_data, colWidths=[4 * cm, 3 * cm, 3 * cm, 3 * cm, 3 * cm])
                    rt.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), BLUE),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
                        ('ROWHEIGHT', (0, 0), (-1, -1), 18),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ]))
                    elements.append(rt)
                else:
                    elements.append(Paragraph('Aucun entretien enregistré.', normal_style))

                # ---- SINISTRES ----
                section_title('Historique des Sinistres', '🚨')
                if sinistres:
                    sin_data = [['Date', 'Type', 'Statut', 'Montant', 'Description']]
                    for s in sinistres[:10]:
                        sin_data.append([
                            str(s.get('date_sinistre') or '—'),
                            s.get('type') or '—',
                            s.get('status') or '—',
                            f"{s.get('montant_reparation') or '—'} DT",
                            (s.get('description') or '—')[:40],
                        ])
                    st = Table(sin_data, colWidths=[3 * cm, 3 * cm, 3 * cm, 3 * cm, 4 * cm])
                    st.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), RED),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
                        ('ROWHEIGHT', (0, 0), (-1, -1), 18),
                        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ]))
                    elements.append(st)
                else:
                    elements.append(Paragraph('Aucun sinistre enregistré.', normal_style))

                # ---- FOOTER ----
                elements.append(Spacer(1, 0.5 * cm))
                elements.append(HRFlowable(width='100%', thickness=1, color=GRAY))
                elements.append(Paragraph(
                    f'ALT Fleet Management — Dossier généré le {datetime.date.today().strftime("%d/%m/%Y")} — Confidentiel',
                    ParagraphStyle('F', parent=styles['Normal'], fontSize=7,
                                   textColor=GRAY, alignment=TA_CENTER)
                ))

                doc.build(elements)
                buffer.seek(0)

                from flask import send_file
                return send_file(
                    buffer,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=f"dossier_{car.get('plate_number', car_id).replace(' ', '_')}.pdf"
                )

            except Exception as e:
                import traceback
                print(traceback.format_exc())
                return jsonify({'status': 'failed', 'message': str(e)}), 500