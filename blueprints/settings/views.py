from flask import Blueprint, request, jsonify
from tools.database_tools import DatabaseTools


class SettingsViews:
    def __init__(self):
        self.db = DatabaseTools()
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
                con, cursor = self.db.find_connection()
                cursor.execute("INSERT INTO car_brands (name) VALUES (%s)", (name,))
                con.commit()
                con.close()
                return jsonify({'status': 'success', 'message': 'Marque ajoutée'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/update-brand/<int:brand_id>', methods=['PUT'])
        def update_brand(brand_id):
            try:
                name = request.get_json().get('name', '').strip()
                if not name:
                    return jsonify({'status': 'failed', 'message': 'Nom requis'})
                con, cursor = self.db.find_connection()
                cursor.execute("UPDATE car_brands SET name=%s WHERE id=%s", (name, brand_id))
                con.commit()
                con.close()
                return jsonify({'status': 'success', 'message': 'Marque mise à jour'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/delete-brand/<int:brand_id>', methods=['DELETE'])
        def delete_brand(brand_id):
            try:
                con, cursor = self.db.find_connection()
                cursor.execute("DELETE FROM car_models WHERE brand_id=%s", (brand_id,))
                cursor.execute("DELETE FROM car_brands WHERE id=%s", (brand_id,))
                con.commit()
                con.close()
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
                con, cursor = self.db.find_connection()
                cursor.execute("INSERT INTO car_models (brand_id, name) VALUES (%s, %s)", (brand_id, name))
                con.commit()
                con.close()
                return jsonify({'status': 'success', 'message': 'Modèle ajouté'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/update-model/<int:model_id>', methods=['PUT'])
        def update_model(model_id):
            try:
                name = request.get_json().get('name', '').strip()
                if not name:
                    return jsonify({'status': 'failed', 'message': 'Nom requis'})
                con, cursor = self.db.find_connection()
                cursor.execute("UPDATE car_models SET name=%s WHERE id=%s", (name, model_id))
                con.commit()
                con.close()
                return jsonify({'status': 'success', 'message': 'Modèle mis à jour'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/delete-model/<int:model_id>', methods=['DELETE'])
        def delete_model(model_id):
            try:
                con, cursor = self.db.find_connection()
                cursor.execute("DELETE FROM car_models WHERE id=%s", (model_id,))
                con.commit()
                con.close()
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
                con, cursor = self.db.find_connection()
                cursor.execute("INSERT INTO departements (name) VALUES (%s)", (name,))
                con.commit()
                con.close()
                return jsonify({'status': 'success', 'message': 'Département ajouté'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/update-dept/<int:dept_id>', methods=['PUT'])
        def update_dept(dept_id):
            try:
                name = request.get_json().get('name', '').strip()
                if not name:
                    return jsonify({'status': 'failed', 'message': 'Nom requis'})
                con, cursor = self.db.find_connection()
                cursor.execute("UPDATE departements SET name=%s WHERE id=%s", (name, dept_id))
                con.commit()
                con.close()
                return jsonify({'status': 'success', 'message': 'Département mis à jour'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/delete-dept/<int:dept_id>', methods=['DELETE'])
        def delete_dept(dept_id):
            try:
                con, cursor = self.db.find_connection()
                cursor.execute("DELETE FROM postes WHERE departement_id=%s", (dept_id,))
                cursor.execute("DELETE FROM departements WHERE id=%s", (dept_id,))
                con.commit()
                con.close()
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
                con, cursor = self.db.find_connection()
                cursor.execute("INSERT INTO postes (departement_id, name) VALUES (%s, %s)", (departement_id, name))
                con.commit()
                con.close()
                return jsonify({'status': 'success', 'message': 'Poste ajouté'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/update-poste/<int:poste_id>', methods=['PUT'])
        def update_poste(poste_id):
            try:
                name = request.get_json().get('name', '').strip()
                if not name:
                    return jsonify({'status': 'failed', 'message': 'Nom requis'})
                con, cursor = self.db.find_connection()
                cursor.execute("UPDATE postes SET name=%s WHERE id=%s", (name, poste_id))
                con.commit()
                con.close()
                return jsonify({'status': 'success', 'message': 'Poste mis à jour'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.settings_bp.route('/delete-poste/<int:poste_id>', methods=['DELETE'])
        def delete_poste(poste_id):
            try:
                con, cursor = self.db.find_connection()
                cursor.execute("DELETE FROM postes WHERE id=%s", (poste_id,))
                con.commit()
                con.close()
                return jsonify({'status': 'success', 'message': 'Poste supprimé'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500