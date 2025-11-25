from services.voiture import VoitureService
from flask import Blueprint, request, jsonify


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

            carte_grise = request.files.get('carte_grise')

            # Vérification champs obligatoires
            if not model:
                return {'status': 'failed', 'message': 'Le modèle est requis'}
            if not year:
                return {'status': 'failed', 'message': "L'année est requise"}
            if not plate_number:
                return {'status': 'failed', 'message': "Le numéro d'immatriculation est requis"}
            if not status:
                return {'status': 'failed', 'message': 'Le statut est requis'}
            if not acquisition_date:
                return {'status': 'failed', 'message': "La date d’acquisition est requise"}

            # Appel service
            voiture_id = self.VoitureService.ajouter_voiture(
                model=model,
                year=year,
                plate_number=plate_number,
                owner_name=owner_name,
                chassis_number=chassis_number,
                status=status,
                acquisition_date=acquisition_date,
                registration_date=registration_date,
                expiration_date=expiration_date,
                notes=notes,
                carte_grise=carte_grise
            )

            return {'status': 'success', 'message': 'Voiture ajoutée avec succès', 'voiture_id': voiture_id}

        @self.car_bp.route('/get-cars', methods=['GET'])
        def get_cars():
            # search_by_name = request.args.get('search_by_name', '').strip().lower()
            page = request.args.get('page', 1)
            limit = request.args.get('limit', 10)
            # print(f"Search by name: {search_by_name}, Page: {page}, Limit: {limit}")
            try:
                page = int(page)
                limit = int(limit)
            except ValueError:
                return jsonify({'status': 'failed', 'message': 'Page and limit must be integers'})
            begin = (page - 1) * limit
            data, count = self.VoitureService.get_cars(number=limit,
                                                       begin=begin, dict_form=True)

            if data is not None and len(data) == 0:
                return jsonify({'status': 'failed', 'message': data})
            print(f"Retrieved  cars out of {count} matching the criteria.")
            print(data)
            return jsonify({
                'status': 'success',
                'data': data,
                'count': count
            })
