from flask import Blueprint, render_template, request, jsonify, session, redirect

# Create (or update) your blueprint
bp = Blueprint(
    'main',
    __name__,
    url_prefix='',
    template_folder='templates'
)

# Dashboard route
@bp.route('/', methods=['GET'])
def dashboard():
    # renders templates/dash.html
    return render_template('dash.html')

# You can keep any other API routes here too:
@bp.route('/api/data', methods=['POST'])
def data_api():
    payload = request.get_json()
    return jsonify({"status": "ok", "received": payload})
