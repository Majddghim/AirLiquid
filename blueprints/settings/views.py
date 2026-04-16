from flask import Blueprint, request, jsonify
from services.settings import SettingsService


class SettingsViews:
    def __init__(self):
        self.service = SettingsService()
        self.settings_bp = Blueprint('settings', __name__)
        self.settings_routes()

    def settings_routes(self):

        # ------------------------------------------------------------------ #
        # BRANDS                                                               #
        # ------------------------------------------------------------------ #

        @self.settings_bp.route('/add-brand', methods=['POST'])
        def add_brand():
            try:
                name = request.get_json().get('name', '').strip()
                if not name:
                    return jsonify({'status': 'failed', 'message': 'Nom requis'})
                self.service.add_brand(name)
                return jsonify({'status': 'success', 'message': 'Marque ajoutée'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/update-brand/<int:brand_id>', methods=['PUT'])
        def update_brand(brand_id):
            try:
                name = request.get_json().get('name', '').strip()
                if not name:
                    return jsonify({'status': 'failed', 'message': 'Nom requis'})
                self.service.update_brand(brand_id, name)
                return jsonify({'status': 'success', 'message': 'Marque mise à jour'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/delete-brand/<int:brand_id>', methods=['DELETE'])
        def delete_brand(brand_id):
            try:
                self.service.delete_brand(brand_id)
                return jsonify({'status': 'success', 'message': 'Marque supprimée'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # ------------------------------------------------------------------ #
        # MODELS                                                               #
        # ------------------------------------------------------------------ #

        @self.settings_bp.route('/add-model', methods=['POST'])
        def add_model():
            try:
                data     = request.get_json()
                name     = data.get('name', '').strip()
                brand_id = data.get('brand_id')
                if not name or not brand_id:
                    return jsonify({'status': 'failed', 'message': 'Nom et marque requis'})
                self.service.add_model(brand_id, name)
                return jsonify({'status': 'success', 'message': 'Modèle ajouté'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/update-model/<int:model_id>', methods=['PUT'])
        def update_model(model_id):
            try:
                name = request.get_json().get('name', '').strip()
                if not name:
                    return jsonify({'status': 'failed', 'message': 'Nom requis'})
                self.service.update_model(model_id, name)
                return jsonify({'status': 'success', 'message': 'Modèle mis à jour'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/delete-model/<int:model_id>', methods=['DELETE'])
        def delete_model(model_id):
            try:
                self.service.delete_model(model_id)
                return jsonify({'status': 'success', 'message': 'Modèle supprimé'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # ------------------------------------------------------------------ #
        # DÉPARTEMENTS                                                         #
        # ------------------------------------------------------------------ #

        @self.settings_bp.route('/add-dept', methods=['POST'])
        def add_dept():
            try:
                name = request.get_json().get('name', '').strip()
                if not name:
                    return jsonify({'status': 'failed', 'message': 'Nom requis'})
                self.service.add_departement(name)
                return jsonify({'status': 'success', 'message': 'Département ajouté'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/update-dept/<int:dept_id>', methods=['PUT'])
        def update_dept(dept_id):
            try:
                name = request.get_json().get('name', '').strip()
                if not name:
                    return jsonify({'status': 'failed', 'message': 'Nom requis'})
                self.service.update_departement(dept_id, name)
                return jsonify({'status': 'success', 'message': 'Département mis à jour'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/delete-dept/<int:dept_id>', methods=['DELETE'])
        def delete_dept(dept_id):
            try:
                self.service.delete_departement(dept_id)
                return jsonify({'status': 'success', 'message': 'Département supprimé'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # ------------------------------------------------------------------ #
        # POSTES                                                               #
        # ------------------------------------------------------------------ #

        @self.settings_bp.route('/add-poste', methods=['POST'])
        def add_poste():
            try:
                data           = request.get_json()
                name           = data.get('name', '').strip()
                departement_id = data.get('departement_id')
                if not name or not departement_id:
                    return jsonify({'status': 'failed', 'message': 'Nom et département requis'})
                self.service.add_poste(departement_id, name)
                return jsonify({'status': 'success', 'message': 'Poste ajouté'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/update-poste/<int:poste_id>', methods=['PUT'])
        def update_poste(poste_id):
            try:
                name = request.get_json().get('name', '').strip()
                if not name:
                    return jsonify({'status': 'failed', 'message': 'Nom requis'})
                self.service.update_poste(poste_id, name)
                return jsonify({'status': 'success', 'message': 'Poste mis à jour'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/delete-poste/<int:poste_id>', methods=['DELETE'])
        def delete_poste(poste_id):
            try:
                self.service.delete_poste(poste_id)
                return jsonify({'status': 'success', 'message': 'Poste supprimé'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # ------------------------------------------------------------------ #
        # CAR PARTS                                                            #
        # ------------------------------------------------------------------ #

        @self.settings_bp.route('/get-parts', methods=['GET'])
        def get_parts():
            try:
                data = self.service.get_all_parts()
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/add-part', methods=['POST'])
        def add_part():
            try:
                data = request.get_json()
                name = data.get('name', '').strip()
                if not name:
                    return jsonify({'status': 'failed', 'message': 'Nom requis'})
                self.service.add_part(
                    name=name,
                    category=data.get('category'),
                    alert_km_interval=data.get('alert_km_interval'),
                    alert_month_interval=data.get('alert_month_interval'),
                    notes=data.get('notes')
                )
                return jsonify({'status': 'success', 'message': 'Pièce ajoutée'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/update-part/<int:part_id>', methods=['PUT'])
        def update_part(part_id):
            try:
                data = request.get_json()
                name = data.get('name', '').strip()
                if not name:
                    return jsonify({'status': 'failed', 'message': 'Nom requis'})
                self.service.update_part(
                    part_id=part_id,
                    name=name,
                    category=data.get('category'),
                    alert_km_interval=data.get('alert_km_interval'),
                    alert_month_interval=data.get('alert_month_interval'),
                    notes=data.get('notes')
                )
                return jsonify({'status': 'success', 'message': 'Pièce mise à jour'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/delete-part/<int:part_id>', methods=['DELETE'])
        def delete_part(part_id):
            try:
                self.service.delete_part(part_id)
                return jsonify({'status': 'success', 'message': 'Pièce supprimée'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # ------------------------------------------------------------------ #
        # GARAGES                                                              #
        # ------------------------------------------------------------------ #

        @self.settings_bp.route('/get-garages', methods=['GET'])
        def get_garages():
            try:
                data = self.service.get_all_garages()
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/add-garage', methods=['POST'])
        def add_garage():
            try:
                data = request.get_json()
                name = data.get('name', '').strip()
                if not name:
                    return jsonify({'status': 'failed', 'message': 'Nom requis'})
                self.service.add_garage(
                    name=name,
                    type_=data.get('type'),
                    brand=data.get('brand'),
                    phone=data.get('phone'),
                    address=data.get('address'),
                    contact_person=data.get('contact_person')
                )
                return jsonify({'status': 'success', 'message': 'Garage ajouté'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/update-garage/<int:garage_id>', methods=['PUT'])
        def update_garage(garage_id):
            try:
                data = request.get_json()
                name = data.get('name', '').strip()
                if not name:
                    return jsonify({'status': 'failed', 'message': 'Nom requis'})
                self.service.update_garage(
                    garage_id=garage_id,
                    name=name,
                    type_=data.get('type'),
                    brand=data.get('brand'),
                    phone=data.get('phone'),
                    address=data.get('address'),
                    contact_person=data.get('contact_person'),
                    status=data.get('status')
                )
                return jsonify({'status': 'success', 'message': 'Garage mis à jour'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/delete-garage/<int:garage_id>', methods=['DELETE'])
        def delete_garage(garage_id):
            try:
                self.service.delete_garage(garage_id)
                return jsonify({'status': 'success', 'message': 'Garage désactivé'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500