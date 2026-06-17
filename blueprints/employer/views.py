from flask import Blueprint, request, jsonify
from services.employe import EmployeService
from flask import render_template, session, redirect, url_for
from tools.email_tools import send_welcome_email, send_password_changed_email
import os
from werkzeug.utils import secure_filename
from tools.ocr_tools import OCRTools
from services.maintenance import MaintenanceService

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

            if not nom:        return {'status': 'failed', 'message': 'Nom est requis'}
            if not prenom:     return {'status': 'failed', 'message': 'Prenom est requis'}
            if not email:      return {'status': 'failed', 'message': 'Email est requis'}
            if not telephone:  return {'status': 'failed', 'message': 'Telephone est requis'}
            if not poste:      return {'status': 'failed', 'message': 'Poste est requis'}
            if not departement: return {'status': 'failed', 'message': 'Departement est requis'}
            if not created:    return {'status': 'failed', 'message': 'Date de creation est requis'}

            empl = self.EmployeService.get_employe_by_email(email)
            if empl:
                return {'status': 'failed', 'message': 'Employe avec cet email existe déjà'}

            employe_id = self.EmployeService.add_employe(
                nom, prenom, departement, poste, email, telephone, created)

            # generate temp password and send email
            temp_password = self.EmployeService.generate_temp_password()
            self.EmployeService.set_temp_password(employe_id, temp_password)
            send_welcome_email(email, prenom, nom, temp_password)

            return {'status': 'success', 'message': 'Employé ajouté avec succès — identifiants envoyés par email'}

        @self.employe_bp.route('/get-employes', methods=['GET'])
        def get_employes():
            search_by_name = request.args.get('search_by_name', '').strip().lower()
            page  = request.args.get('page', 1)
            limit = request.args.get('limit', 7)
            try:
                page  = int(page)
                limit = int(limit)
            except ValueError:
                return jsonify({'status': 'failed', 'message': 'Page and limit must be integers'})

            begin = (page - 1) * limit
            data, count = self.EmployeService.get_employe_by_name(
                search_by_name, number=limit, begin=begin, dict_form=True)

            if data is None or (isinstance(data, list) and len(data) == 0):
                return jsonify({'status': 'failed', 'message': 'No employees found', 'data': [], 'count': 0})

            return jsonify({'status': 'success', 'data': data, 'count': count})

        @self.employe_bp.route('/get-all-employes', methods=['GET'])
        def get_all_employes():
            data = self.EmployeService.get_all_employes()
            if data is None or (isinstance(data, list) and len(data) == 0):
                return jsonify({'status': 'failed', 'message': 'No employees found', 'data': []})
            return jsonify({'status': 'success', 'data': data})

        # ------------------------------------------------------------------ #
        # DÉPARTEMENTS & POSTES                                                #
        # ------------------------------------------------------------------ #

        @self.employe_bp.route('/get-departements', methods=['GET'])
        def get_departements():
            try:
                data = self.EmployeService.get_departements()
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.employe_bp.route('/get-postes/<int:departement_id>', methods=['GET'])
        def get_postes(departement_id):
            try:
                data = self.EmployeService.get_postes_by_departement(departement_id)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # ------------------------------------------------------------------ #
        # GET, UPDATE, DELETE, AFFECTATION                                     #
        # ------------------------------------------------------------------ #

        @self.employe_bp.route('/get-employe/<int:employe_id>', methods=['GET'])
        def get_employe(employe_id):
            try:
                employe = self.EmployeService.get_employe_by_id(employe_id)
                if not employe:
                    return jsonify({'status': 'failed', 'message': 'Employé introuvable'}), 404
                return jsonify({'status': 'success', 'data': employe.__dict__()})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.employe_bp.route('/update/<int:employe_id>', methods=['PUT'])
        def update_employe(employe_id):
            try:
                data = request.get_json()
                self.EmployeService.update_employe(
                    employe_id=employe_id,
                    nom=data.get('nom'),
                    prenom=data.get('prenom'),
                    email=data.get('email'),
                    telephone=data.get('telephone'),
                    departement=data.get('departement'),
                    poste=data.get('poste')
                )
                return jsonify({'status': 'success', 'message': 'Employé mis à jour avec succès'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.employe_bp.route('/delete/<int:employe_id>', methods=['DELETE'])
        def delete_employe(employe_id):
            try:
                self.EmployeService.supprimer_employe(employe_id)
                return jsonify({'status': 'success', 'message': 'Employé désactivé avec succès'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.employe_bp.route('/get-affectation-active/<int:employe_id>', methods=['GET'])
        def get_affectation_active(employe_id):
            try:
                data = self.EmployeService.get_affectation_active(employe_id)
                if data:
                    return jsonify({'status': 'success', 'assigned': True, 'data': data})
                return jsonify({'status': 'success', 'assigned': False})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.employe_bp.route('/profil/<int:employe_id>', methods=['GET'])
        def profil_page(employe_id):
            from flask import render_template
            return render_template('employe-profil.html')

        @self.employe_bp.route('/profil-data/<int:employe_id>', methods=['GET'])
        def profil_data(employe_id):
            try:
                data = self.EmployeService.get_profil_employe(employe_id)
                if not data:
                    return jsonify({'status': 'failed', 'message': 'Employé introuvable'}), 404
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500



        @self.employe_bp.route('/login', methods=['GET'])
        def login_page():
            if 'employe_id' in session:
                return redirect('/employe/dashboard')
            return render_template('employe-login.html')

        @self.employe_bp.route('/login', methods=['POST'])
        def login():
            try:
                data = request.get_json()
                email = data.get('email')
                password = data.get('password')
                if not email or not password:
                    return jsonify({'status': 'failed', 'message': 'Email et mot de passe requis'})

                emp, error = self.EmployeService.authenticate_employee(email, password)
                if error:
                    return jsonify({'status': 'failed', 'message': error})

                session['employe_id'] = emp['id']
                session['employe_nom'] = f"{emp['prenom']} {emp['nom']}"

                if emp['must_change_password']:
                    return jsonify({'status': 'success', 'redirect': '/employe/change-password'})
                return jsonify({'status': 'success', 'redirect': '/employe/dashboard'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.employe_bp.route('/logout', methods=['GET'])
        def employe_logout():
            session.pop('employe_id', None)
            session.pop('employe_nom', None)
            return redirect('/employe/login')

        @self.employe_bp.route('/change-password', methods=['GET'])
        def change_password_page():
            if 'employe_id' not in session:
                return redirect('/employe/login')
            return render_template('employe-change-password.html')

        @self.employe_bp.route('/change-password', methods=['POST'])
        def change_password():
            try:
                if 'employe_id' not in session:
                    return jsonify({'status': 'failed', 'message': 'Non connecté'})
                data = request.get_json()
                new_password = data.get('new_password')
                confirm = data.get('confirm_password')
                if not new_password or len(new_password) < 6:
                    return jsonify({'status': 'failed', 'message': 'Mot de passe trop court (6 caractères minimum)'})
                if new_password != confirm:
                    return jsonify({'status': 'failed', 'message': 'Les mots de passe ne correspondent pas'})

                emp_id = session['employe_id']
                self.EmployeService.change_password(emp_id, new_password)

                # send confirmation email
                emp = self.EmployeService.get_employe_by_id(emp_id)
                if emp:
                    send_password_changed_email(emp.email, emp.prenom, emp.nom)

                return jsonify({'status': 'success', 'redirect': '/employe/dashboard'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.employe_bp.route('/dashboard', methods=['GET'])
        def dashboard():
            if 'employe_id' not in session:
                return redirect('/employe/login')
            return render_template('employe-dashboard.html')

        @self.employe_bp.route('/dashboard-data', methods=['GET'])
        def dashboard_data():
            try:
                if 'employe_id' not in session:
                    return jsonify({'status': 'failed', 'message': 'Non connecté'}), 401
                data = self.EmployeService.get_employee_mobile_data(session['employe_id'])
                if not data:
                    return jsonify({'status': 'failed', 'message': 'Données introuvables'}), 404
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # add in employe_routes():

        @self.employe_bp.route('/upload-odometer-photo/<int:car_id>', methods=['POST'])
        def upload_odometer_photo(car_id):
            try:
                if 'employe_id' not in session:
                    return jsonify({'status': 'failed', 'message': 'Non connecté'}), 401

                if 'file' not in request.files:
                    return jsonify({'status': 'failed', 'message': 'Aucun fichier reçu'})

                file = request.files['file']
                if file.filename == '':
                    return jsonify({'status': 'failed', 'message': 'Fichier vide'})

                upload_folder = 'static/uploads/odometer'
                os.makedirs(upload_folder, exist_ok=True)
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                return jsonify({
                    'status': 'success',
                    'file_path': file_path
                })

            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.employe_bp.route('/update-km/<int:car_id>', methods=['POST'])
        def update_km(car_id):
            try:
                if 'employe_id' not in session:
                    return jsonify({'status': 'failed', 'message': 'Non connecté'}), 401

                data = request.get_json()
                km = data.get('km')
                file_path = data.get('file_path')

                if not km:
                    return jsonify({'status': 'failed', 'message': 'KM requis'})

                maintenance_service = MaintenanceService()
                con, cursor = maintenance_service.db.find_connection()
                try:
                    cursor.execute("""
                        INSERT INTO car_km (car_id, km, recorded_at, notes, file_path)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        car_id, int(km),
                        __import__('datetime').date.today().isoformat(),
                        f"Relevé par employé via app mobile",
                        file_path or None
                    ))
                    con.commit()
                finally:
                    con.close()

                return jsonify({'status': 'success', 'message': 'Kilométrage mis à jour'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.employe_bp.route('/report-problem/<int:car_id>', methods=['POST'])
        def report_problem(car_id):
            try:
                if 'employe_id' not in session:
                    return jsonify({'status': 'failed', 'message': 'Non connecté'}), 401

                description = request.form.get('description', '').strip()
                ai_analysis = request.form.get('ai_analysis', '').strip()
                file_path = None

                if 'file' in request.files:
                    file = request.files['file']
                    if file and file.filename != '':
                        upload_folder = 'static/uploads/problems'
                        os.makedirs(upload_folder, exist_ok=True)
                        filename = secure_filename(file.filename)
                        file_path = os.path.join(upload_folder, filename)
                        file.save(file_path)

                # save as a sinistre with type 'autre' and status 'ouvert'
                from services.sinistre import SinistreService
                sinistre_service = SinistreService()
                full_description = f"[Signalement employé]\n{ai_analysis}\n\nDescription: {description}" if ai_analysis else description

                sinistre_service.declarer_sinistre(
                    car_id=car_id,
                    employee_id=session['employe_id'],
                    date_sinistre=__import__('datetime').date.today().isoformat(),
                    type_sinistre='autre',
                    description=full_description,
                    n_constat=None,
                    date_constat=None,
                    file_path=file_path,
                    set_maintenance=False,
                    replacement_car_id=None,
                    prise_en_charge='societe'
                )

                return jsonify({'status': 'success', 'message': 'Problème signalé avec succès'})

            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.employe_bp.route('/analyze-problem', methods=['POST'])
        def analyze_problem():
            try:
                if 'employe_id' not in session:
                    return jsonify({'status': 'failed', 'message': 'Non connecté'}), 401

                if 'file' not in request.files:
                    return jsonify({'status': 'failed', 'message': 'Aucun fichier reçu'})

                file = request.files['file']
                if file.filename == '':
                    return jsonify({'status': 'failed', 'message': 'Fichier vide'})

                upload_folder = 'static/uploads/problems'
                os.makedirs(upload_folder, exist_ok=True)
                filename = secure_filename(file.filename)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                ocr = OCRTools()
                result = ocr.analyze_car_damage(file_path)

                return jsonify({
                    'status': 'success',
                    'analysis': result.get('description', ''),
                    'severity': result.get('severity', 'unknown'),
                    'file_path': file_path
                })

            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.employe_bp.route('/documents/<int:car_id>', methods=['GET'])
        def get_documents(car_id):
            try:
                if 'employe_id' not in session:
                    return jsonify({'status': 'failed', 'message': 'Non connecté'}), 401
                data = self.EmployeService.get_employee_documents(car_id)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.employe_bp.route('/maintenance/<int:car_id>', methods=['GET'])
        def get_maintenance(car_id):
            try:
                if 'employe_id' not in session:
                    return jsonify({'status': 'failed', 'message': 'Non connecté'}), 401
                data = self.EmployeService.get_employee_maintenance(car_id)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.employe_bp.route('/emergency-contacts', methods=['GET'])
        def emergency_contacts():
            try:
                if 'employe_id' not in session:
                    return jsonify({'status': 'failed', 'message': 'Non connecté'}), 401
                garages = self.EmployeService.get_emergency_contacts()
                return jsonify({'status': 'success', 'data': garages})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500