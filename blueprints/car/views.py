from services.voiture import VoitureService
from flask import Blueprint, request, jsonify, render_template


class CarViews:
    def __init__(self):
        self.VoitureService = VoitureService()
        self.car_bp = Blueprint('car', __name__)
        self.car_routes()

    def car_routes(self):

        @self.car_bp.route('/ajout-voiture', methods=['POST'])
        def ajout_voiture():
            model = request.form.get('model')
            year = request.form.get('year')
            plate_number = request.form.get('plate_number')
            owner_name = request.form.get('owner_name')
            chassis_number = request.form.get('chassis_number')
            status = request.form.get('status')
            acquisition_date = request.form.get('acquisition_date')
            registration_date = request.form.get('registration_date')
            expiration_date = request.form.get('expiration_date')
            notes = request.form.get('notes')

            # Handle File Upload
            file_path = None
            if 'carte_grise' in request.files:
                file = request.files['carte_grise']
                if file.filename != '':
                    import os
                    from werkzeug.utils import secure_filename
                    upload_folder = 'static/uploads/carte_grises'
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)
                    filename = secure_filename(f"{plate_number}_{file.filename}")
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)

            if not model or not year or not plate_number or not status:
                return jsonify({'status': 'failed', 'message': 'Veuillez remplir les champs obligatoires'})

            try:
                voiture_id = self.VoitureService.ajouter_voiture(
                    model=model,
                    year=year,
                    plate_number=plate_number,
                    owner_name=owner_name,
                    chassis_number=chassis_number,
                    status=status,
                    registration_date=registration_date,
                    expiration_date=expiration_date,
                    acquisition_date=acquisition_date,
                    notes=notes,
                    file_path=file_path
                )
                
                # If we have a file_path, we should update the carte_grises table or pass it to service
                # For now, let's assume the service handles it or we'll update it.
                
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

            # 🛠️ MOCK AI EXTRACTION
            # In production: Use Google Vision API, Tesseract, or an LLM
            mock_data = {
                "model": "Peugeot Partner",
                "year": "2021",
                "plate_number": "154 TU 9876",
                "owner_name": "AIR LIQUID S.A",
                "chassis_number": "VN7890BC123456",
                "registration_date": "2021-03-20",
                "expiration_date": "2025-03-20"
            }

            import time
            time.sleep(1.5) # Simulate processing time

            return jsonify({
                'status': 'success',
                'extracted_data': mock_data,
                'message': 'Données extraites par IA'
            })

        @self.car_bp.route('/get-voitures', methods=['GET'])
        def get_voitures():
            search_by_name = request.args.get('search_by_name', '').strip()
            page = request.args.get('page', 1, type=int)
            limit = request.args.get('limit', 10, type=int)
            
            try:
                offset = (page - 1) * limit
                voitures, total_count = self.VoitureService.get_voitures_paginated(
                    search_by_name=search_by_name,
                    limit=limit,
                    offset=offset
                )
                return jsonify({
                    'status': 'success', 
                    'data': voitures, 
                    'count': total_count
                })
            except Exception as e:
                import traceback
                print(traceback.format_exc())
                return jsonify({'status': 'failed', 'message': str(e)}), 500

