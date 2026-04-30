from flask import Blueprint, request, jsonify, render_template, send_file, session, redirect
from services.report_service import ReportService
from tools.report_tools import ReportTools
import datetime


class ReportViews:
    def __init__(self):
        self.service      = ReportService()
        self.report_tools = ReportTools()
        self.reports_bp   = Blueprint('reports', __name__)
        self.report_routes()

    def report_routes(self):

        @self.reports_bp.route('/', methods=['GET'])
        def reports_page():
            if 'user_id' not in session:
                return redirect('/auth/login')
            return render_template('reports.html')

        @self.reports_bp.route('/analyze', methods=['POST'])
        def analyze_request():
            try:
                data         = request.get_json()
                request_text = data.get('request')
                if not request_text:
                    return jsonify({'status': 'failed', 'message': 'Demande vide'})

                result = self.report_tools.understand_report_request(request_text)

                if 'error' in result:
                    return jsonify({'status': 'failed', 'message': result['error']})

                if 'sql' not in result or 'title' not in result:
                    return jsonify({'status': 'failed', 'message': 'Réponse invalide du modèle'})

                return jsonify({
                    'status': 'success',
                    'title':  result['title'],
                    'sql':    result['sql']
                })
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.reports_bp.route('/generate', methods=['POST'])
        def generate_report():
            try:
                data   = request.get_json()
                sql    = data.get('sql')
                title  = data.get('title', 'Rapport')
                fmt    = data.get('format', 'pdf')

                if not sql:
                    return jsonify({'status': 'failed', 'message': 'SQL manquant'})

                headers, rows = self.service.execute_report_query(sql)

                # convert all values to strings for PDF/Excel
                str_rows = []
                for row in rows:
                    str_row = []
                    for val in row:
                        if val is None:
                            str_row.append('—')
                        else:
                            str_row.append(str(val))
                    str_rows.append(str_row)

                if fmt == 'excel':
                    buffer   = self.report_tools.generate_excel(title, headers, str_rows)
                    filename = f"rapport_{datetime.date.today()}.xlsx"
                    return send_file(
                        buffer, as_attachment=True, download_name=filename,
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    )
                else:
                    buffer   = self.report_tools.generate_pdf(
                        title, '', headers, str_rows,
                        f"Généré le {datetime.date.today().strftime('%d/%m/%Y')}"
                    )
                    filename = f"rapport_{datetime.date.today()}.pdf"
                    return send_file(
                        buffer, as_attachment=True, download_name=filename,
                        mimetype='application/pdf'
                    )

            except ValueError as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 400
            except Exception as e:
                import traceback
                traceback.print_exc()
                return jsonify({'status': 'failed', 'message': str(e)}), 500