from flask import Blueprint, request, jsonify
from services.employe import EmployeService


class employe:
    def __init__(self):
        self.EmployeService = EmployeService()
        self.employe_bp = Blueprint('employe', __name__)
        self.employe_routes()

    def employe_routes(self):
        @self.employe_bp.route('/ajout-employe', methods=['POST'])
        def ajout():
            data = request.get_json()
            nom = data.get('nom')
            prenom = data.get('prenom')
            email = data.get('email')
            telephone = data.get('telephone')
            poste = data.get('poste')
            departement = data.get('departement')
            created = data.get('created_at')
            if not nom:
                print("name missing")
                return {'status': 'failed', 'message': 'Nom est requis'}
            if not prenom:
                print("prenom missing")
                return {'status': 'failed', 'message': 'Prenom est requis'}
            if not email:
                print("email missing")
                return {'status': 'failed', 'message': 'Email est requis'}
            if not telephone:
                print("telephone missing")
                return {'status': 'failed', 'message': 'Telephone est requis'}
            if not poste:
                print("poste missing")
                return {'status': 'failed', 'message': 'Poste est requis'}
            if not departement:
                print("departement missing")
                return {'status': 'failed', 'message': 'Departement est requis'}
            if not created:
                print("created_at missing")
                return {'status': 'failed', 'message': 'Date de creation est requis'}

            empl = self.EmployeService.get_employe_by_email(email)
            if empl is not None:
                return {'status': 'failed', 'message': 'Employe avec cet email existe déjà'}

            self.EmployeService.add_employe(nom, prenom, departement, poste, email, telephone, created)

            return {'status': 'success', 'message': 'Employe ajouté avec succès'}



        """
        def get_employes():
            search_by_name = request.args.get('search_by_name', '').strip().lower()
            page = request.args.get('page', 1)
            limit = request.args.get('limit', 10)
            print(f"Search by name: {search_by_name}, Page: {page}, Limit: {limit}")
            try:
                page = int(page)
                limit = int(limit)
            except ValueError:
                return jsonify({'status': 'failed', 'message': 'Page and limit must be integers'})
            begin = (page - 1) * limit
            data, count = self.EmployeService.get_employe_by_name(search_by_name, number=limit,
                                                                                 begin=begin, dict_form=True)

            if data is not None and  len(data) == 0  :
                return jsonify({'status': 'failed', 'message': data})
            print(f"Retrieved {len(data)} employes out of {count} matching the criteria.")
            print(data)
            return jsonify({
                'status': 'success',
                'data': data,
                'count': count
            })"""

        @self.employe_bp.route('/get-employes', methods=['GET'])
        def get_employes():
            data = self.EmployeService.get_all_employes()
            if data is None or len(data) == 0:
                return jsonify({'status': 'failed', 'message': 'No employes found'})
            return jsonify({'status': 'success', 'data': data})
