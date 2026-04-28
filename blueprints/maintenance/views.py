from flask import Blueprint, request, jsonify, render_template_string
from services.maintenance import MaintenanceService
import os
from werkzeug.utils import secure_filename


class MaintenanceViews:
    def __init__(self):
        self.service = MaintenanceService()
        self.maintenance_bp = Blueprint('maintenance', __name__)
        self.maintenance_routes()

    def maintenance_routes(self):

        # ------------------------------------------------------------------ #
        # ALERTS                                                               #
        # ------------------------------------------------------------------ #

        @self.maintenance_bp.route('/alerts/<int:car_id>', methods=['GET'])
        def get_alerts(car_id):
            try:
                data = self.service.get_alerts_by_car(car_id)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.maintenance_bp.route('/all-alerts', methods=['GET'])
        def get_all_alerts():
            try:
                data = self.service.get_all_open_alerts()
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # ------------------------------------------------------------------ #
        # RECORDS                                                              #
        # ------------------------------------------------------------------ #

        @self.maintenance_bp.route('/records/<int:car_id>', methods=['GET'])
        def get_records(car_id):
            try:
                data = self.service.get_records_by_car(car_id)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.maintenance_bp.route('/log/<int:car_id>', methods=['POST'])
        @self.maintenance_bp.route('/log/<int:car_id>', methods=['POST'])
        def log_maintenance(car_id):
            try:
                data = request.get_json()
                record_id = self.service.log_maintenance(
                    car_id=car_id,
                    part_id=data.get('part_id'),
                    garage_id=data.get('garage_id'),
                    done_at=data.get('done_at'),
                    km_at_service=data.get('km_at_service'),
                    next_due_date=data.get('next_due_date'),
                    next_due_km=data.get('next_due_km'),
                    notes=data.get('notes'),
                    alert_id=int(data.get('alert_id')) if data.get('alert_id') else None
                )
                return jsonify({'status': 'success', 'message': 'Entretien enregistré', 'record_id': record_id})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # ------------------------------------------------------------------ #
        # FACTURES                                                             #
        # ------------------------------------------------------------------ #

        @self.maintenance_bp.route('/facture/<int:record_id>', methods=['GET'])
        def get_facture(record_id):
            try:
                data = self.service.get_facture_by_record(record_id)
                if data:
                    return jsonify({'status': 'success', 'data': data})
                return jsonify({'status': 'success', 'data': None})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.maintenance_bp.route('/facture/attach/<int:record_id>', methods=['POST'])
        def attach_facture(record_id):
            try:
                car_id = request.form.get('car_id')
                file_path = None

                if 'file' in request.files:
                    file = request.files['file']
                    if file and file.filename != '':
                        upload_folder = 'static/uploads/factures/maintenance'
                        os.makedirs(upload_folder, exist_ok=True)
                        filename  = secure_filename(file.filename)
                        file_path = os.path.join(upload_folder, filename)
                        file.save(file_path)

                self.service.attach_facture(
                    record_id=record_id,
                    car_id=car_id,
                    num_facture=request.form.get('num_facture'),
                    num_reglement=request.form.get('num_reglement'),
                    date_facture=request.form.get('date_facture'),
                    date_reglement=request.form.get('date_reglement'),
                    montant_ht=request.form.get('montant_ht'),
                    montant_ttc=request.form.get('montant_ttc'),
                    tva=request.form.get('tva'),
                    file_path=file_path
                )
                return jsonify({'status': 'success', 'message': 'Facture attachée avec succès'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # ------------------------------------------------------------------ #
        # BON DE COMMANDE DATA                                                 #
        # ------------------------------------------------------------------ #

        @self.maintenance_bp.route('/bon-data/<int:car_id>', methods=['GET'])
        def get_bon_data(car_id):
            try:
                data = self.service.get_bon_data(car_id)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.maintenance_bp.route('/bon/generate', methods=['POST'])
        def generate_bon():
            try:
                data = request.get_json()
                car = data.get('car')
                garage = data.get('garage')
                items = data.get('items', [])
                date = data.get('date')

                # build rows separately to avoid nested f-string issue
                rows = ""
                for i, item in enumerate(items):
                    rows += f"""
                    <tr>
                        <td>{i + 1}</td>
                        <td><strong>{item.get('part_name', '—')}</strong></td>
                        <td>{item.get('category', '—')}</td>
                        <td>{item.get('notes', '')}</td>
                    </tr>"""

                html = f"""<!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="utf-8">
            <title>Bon de Commande — {car.get('plate_number', '')}</title>
            <style>
                * {{ margin: 0; padding: 0; box-sizing: border-box; }}
                body {{ font-family: 'Arial', sans-serif; font-size: 13px; color: #333; padding: 40px; }}
                .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; border-bottom: 3px solid #0d6efd; padding-bottom: 20px; }}
                .company-name {{ font-size: 22px; font-weight: bold; color: #0d6efd; }}
                .company-sub {{ font-size: 12px; color: #666; margin-top: 4px; }}
                .bon-title {{ font-size: 18px; font-weight: bold; text-align: right; }}
                .bon-num {{ font-size: 12px; color: #888; text-align: right; margin-top: 4px; }}
                .section {{ margin-bottom: 24px; }}
                .section-title {{ font-size: 12px; font-weight: bold; text-transform: uppercase; color: #888; margin-bottom: 10px; letter-spacing: 1px; border-bottom: 1px solid #eee; padding-bottom: 6px; }}
                .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
                .info-item label {{ font-size: 11px; color: #888; display: block; margin-bottom: 2px; }}
                .info-item span {{ font-weight: 600; font-size: 13px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
                thead tr {{ background: #0d6efd; color: white; }}
                thead th {{ padding: 10px 12px; text-align: left; font-size: 12px; }}
                tbody tr {{ border-bottom: 1px solid #eee; }}
                tbody tr:nth-child(even) {{ background: #f8f9fa; }}
                tbody td {{ padding: 10px 12px; font-size: 13px; }}
                .footer {{ margin-top: 40px; display: grid; grid-template-columns: 1fr 1fr; gap: 40px; }}
                .signature-box {{ border: 1px solid #ddd; border-radius: 8px; padding: 16px; min-height: 80px; }}
                .signature-label {{ font-size: 11px; font-weight: bold; text-transform: uppercase; color: #888; margin-bottom: 8px; }}
                .badge {{ display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; }}
                .badge-warning {{ background: #fff3cd; color: #856404; }}
                .badge-info {{ background: #cff4fc; color: #055160; }}
                @media print {{
                    body {{ padding: 20px; }}
                    .no-print {{ display: none; }}
                }}
            </style>
        </head>
        <body>

            <div class="header">
                <div>
                    <div class="company-name">AIR LIQUIDE TUNISIA</div>
                    <div class="company-sub">Gestion de Flotte</div>
                </div>
                <div>
                    <div class="bon-title">BON DE COMMANDE</div>
                    <div class="bon-num">Date: {date}</div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Véhicule</div>
                <div class="info-grid">
                    <div class="info-item"><label>Modèle</label><span>{car.get('model', '—')} {car.get('brand', '')}</span></div>
                    <div class="info-item"><label>Immatriculation</label><span>{car.get('plate_number', '—')}</span></div>
                    <div class="info-item"><label>Année</label><span>{car.get('year', '—')}</span></div>
                    <div class="info-item"><label>Propriétaire</label><span>{car.get('owner_name', '—')}</span></div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Garage</div>
                <div class="info-grid">
                    <div class="info-item"><label>Nom</label><span>{garage.get('name', '—')}</span></div>
                    <div class="info-item"><label>Téléphone</label><span>{garage.get('phone', '—')}</span></div>
                    <div class="info-item"><label>Adresse</label><span>{garage.get('address', '—')}</span></div>
                    <div class="info-item"><label>Contact</label><span>{garage.get('contact_person', '—')}</span></div>
                </div>
            </div>

            <div class="section">
                <div class="section-title">Travaux à effectuer</div>
                <table>
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Pièce / Travail</th>
                            <th>Catégorie</th>
                            <th>Remarques</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows}
                    </tbody>
                </table>
            </div>

            <div class="footer">
                <div class="signature-box">
                    <div class="signature-label">Signature Responsable Fleet</div>
                </div>
                <div class="signature-box">
                    <div class="signature-label">Signature Garage</div>
                </div>
            </div>

            <script>window.onload = () => window.print();</script>
        </body>
        </html>"""

                return html, 200, {'Content-Type': 'text/html; charset=utf-8'}
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        # ------------------------------------------------------------------ #
        # KM TRACKING                                                          #
        # ------------------------------------------------------------------ #

        @self.maintenance_bp.route('/current-km/<int:car_id>', methods=['GET'])
        def get_current_km(car_id):
            try:
                data = self.service.get_current_km(car_id)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.maintenance_bp.route('/km-history/<int:car_id>', methods=['GET'])
        def get_km_history(car_id):
            try:
                data = self.service.get_km_history(car_id)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.maintenance_bp.route('/log-km/<int:car_id>', methods=['POST'])
        def log_km(car_id):
            try:
                data = request.get_json()
                km = data.get('km')
                if not km:
                    return jsonify({'status': 'failed', 'message': 'KM requis'})
                self.service.log_km(
                    car_id=car_id,
                    km=km,
                    recorded_at=data.get('recorded_at'),
                    notes=data.get('notes')
                )
                return jsonify({'status': 'success', 'message': 'KM enregistré'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.maintenance_bp.route('/part-intervals/<int:part_id>', methods=['GET'])
        def get_part_intervals(part_id):
            try:
                data = self.service.get_part_intervals(part_id)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500