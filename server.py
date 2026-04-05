from flask import Flask, request, Response
from threading import Thread
from api import Api
from flask_httpauth import HTTPBasicAuth
import json

from models import Options


class Server:
    def __init__(self, monitor=None):
        self.is_running = False
        self.app = None
        self.auth = None
        self.server_process = None
        self.monitor = monitor

    def run_flask(self):
        self.app = Flask(__name__)
        self.auth = HTTPBasicAuth()

        @self.auth.error_handler
        def auth_error(status):
            return {'status': 'error', 'message': 'Unauthorized'}, status

        @self.auth.verify_password
        def verify_password(username, password):
            if Options.check_username(username) and Options.check_password(password):
                return username
            return False

        @self.app.route('/api/<action>', methods=['GET', 'POST'])
        @self.auth.login_required
        def api(action):
            self.api = Api(self.monitor)
            try:
                return Response(json.dumps(self.api.start_routes(action, request)), content_type='application/json')
            except Exception as e:
                self.api = None
                print(e)
                return Response(json.dumps({'error': True, 'message': 'Server error'}), content_type='application/json', status=500)

        self.app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

    def run_server(self):
        if self.server_process is None:
            self.server_process = Thread(target=self.run_flask, daemon=True)
            self.server_process.start()
