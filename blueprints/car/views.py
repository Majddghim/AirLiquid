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


            # Appel service
            voiture_id = self.VoitureService.ajouter_carte_grise(
                model=model,
                year=year,
                plate_number=plate_number,
                owner_name=owner_name,
                chassis_number=chassis_number,
                status=status,
                registration_date=registration_date,
                expiration_date=expiration_date,
            )

            return {'status': 'success', 'message': 'Voiture ajoutée avec succès', 'voiture_id': voiture_id}




