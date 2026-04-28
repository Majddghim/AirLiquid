from flask import Blueprint, request, jsonify
from services.sinistre import SinistreService
import os
from werkzeug.utils import secure_filename


class SinistreViews:
    def __init__(self):
        self.service = SinistreService()
        self.sinistre_bp = Blueprint('sinistre', __name__)
        self.sinistre_routes()

    def sinistre_routes(self):

        # ------------------------------------------------------------------ #
        # SINISTRES                                                            #
        # ------------------------------------------------------------------ #

        @self.sinistre_bp.route('/by-car/<int:car_id>', methods=['GET'])
        def get_sinistres(car_id):
            try:
                data = self.service.get_sinistres_by_car(car_id)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.sinistre_bp.route('/get/<int:sinistre_id>', methods=['GET'])
        def get_sinistre(sinistre_id):
            try:
                data = self.service.get_sinistre_by_id(sinistre_id)
                if not data:
                    return jsonify({'status': 'failed', 'message': 'Sinistre introuvable'}), 404
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.sinistre_bp.route('/declarer/<int:car_id>', methods=['POST'])
        def declarer_sinistre(car_id):
            try:
                file_path = None
                if 'constat_file' in request.files:
                    file = request.files['constat_file']
                    if file and file.filename != '':
                        upload_folder = 'static/uploads/sinistres/constats'
                        os.makedirs(upload_folder, exist_ok=True)
                        filename  = secure_filename(file.filename)
                        file_path = os.path.join(upload_folder, filename)
                        file.save(file_path)

                sinistre_id = self.service.declarer_sinistre(
                    car_id=car_id,
                    employee_id=request.form.get('employee_id') or None,
                    date_sinistre=request.form.get('date_sinistre'),
                    type_sinistre=request.form.get('type_sinistre'),
                    description=request.form.get('description'),
                    n_constat=request.form.get('n_constat'),
                    date_constat=request.form.get('date_constat'),
                    file_path=file_path,
                    set_maintenance=request.form.get('set_maintenance') == 'true',
                    prise_en_charge=request.form.get('prise_en_charge'),
                    replacement_car_id=request.form.get('replacement_car_id') or None
                )
                return jsonify({
                    'status': 'success',
                    'message': 'Sinistre déclaré avec succès',
                    'sinistre_id': sinistre_id
                })
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.sinistre_bp.route('/update-status/<int:sinistre_id>', methods=['PUT'])
        def update_status(sinistre_id):
            try:
                status = request.get_json().get('status')
                if status not in ['ouvert', 'en_cours', 'cloture']:
                    return jsonify({'status': 'failed', 'message': 'Statut invalide'})
                self.service.update_sinistre_status(sinistre_id, status)
                return jsonify({'status': 'success', 'message': 'Statut mis à jour'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.sinistre_bp.route('/cloturer/<int:sinistre_id>', methods=['POST'])
        def cloturer_sinistre(sinistre_id):
            try:
                data = request.get_json()
                self.service.cloturer_sinistre(
                    sinistre_id=sinistre_id,
                    car_id=data.get('car_id'),
                    employee_id=data.get('employee_id'),
                    montant_reparation=data.get('montant_reparation'),
                    mode_reglement=data.get('mode_reglement'),
                    n_cheque_or_virement=data.get('n_cheque_or_virement'),
                    date_reglement=data.get('date_reglement'),
                    retourner_vehicule=data.get('retourner_vehicule', False),
                    replacement_car_id=data.get('replacement_car_id')
                )
                return jsonify({'status': 'success', 'message': 'Sinistre clôturé avec succès'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # ------------------------------------------------------------------ #
        # FACTURES                                                             #
        # ------------------------------------------------------------------ #

        @self.sinistre_bp.route('/facture/<int:sinistre_id>', methods=['GET'])
        def get_facture(sinistre_id):
            try:
                data = self.service.get_facture_by_sinistre(sinistre_id)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.sinistre_bp.route('/facture/attach/<int:sinistre_id>', methods=['POST'])
        def attach_facture(sinistre_id):
            try:
                file_path = None
                if 'file' in request.files:
                    file = request.files['file']
                    if file and file.filename != '':
                        upload_folder = 'static/uploads/factures/sinistres'
                        os.makedirs(upload_folder, exist_ok=True)
                        filename  = secure_filename(file.filename)
                        file_path = os.path.join(upload_folder, filename)
                        file.save(file_path)

                self.service.attach_facture(
                    sinistre_id=sinistre_id,
                    car_id=request.form.get('car_id'),
                    num_facture=request.form.get('num_facture'),
                    num_reglement=request.form.get('num_reglement'),
                    date_facture=request.form.get('date_facture'),
                    date_reglement=request.form.get('date_reglement'),
                    montant_ht=request.form.get('montant_ht'),
                    montant_ttc=request.form.get('montant_ttc'),
                    tva=request.form.get('tva'),
                    prise_en_charge=request.form.get('prise_en_charge'),
                    file_path=file_path
                )
                return jsonify({'status': 'success', 'message': 'Facture attachée avec succès'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # ------------------------------------------------------------------ #
        # HELPERS                                                              #
        # ------------------------------------------------------------------ #

        @self.sinistre_bp.route('/available-cars', methods=['GET'])
        def get_available_cars():
            try:
                data = self.service.get_available_replacement_cars()
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.sinistre_bp.route('/all', methods=['GET'])
        def get_all_sinistres():
            try:
                data = self.service.get_all_sinistres()
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500