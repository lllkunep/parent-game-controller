from flask import Flask, request, Response
from multiprocessing import Process
from time import sleep
from api import Api
from flask_httpauth import HTTPBasicAuth
import json

from models import Options
from modules.db.db_adapter import DbAdapter


class Server:
    def __init__(self):
        self.is_running = False
        self.app = None
        self.auth = None
        self.server_process = None
        self.status = 'ok'

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
            if action == 'clear-errors':
                self.status = 'ok'
                return Response(json.dumps({'message':'ok'}), content_type='application/json')
            self.api = Api()
            self.api.status = self.status
            try:
                return Response(json.dumps(self.api.start_routes(action, request)), content_type='application/json')
            except Exception as e:
                self.api = None
                print(e)
                return Response(json.dumps({'error': True, 'message': 'Server error'}), content_type='application/json', status=500)

        self.app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

    def run_server(self):
        if self.server_process is None:
            self.server_process = Process(target=self.run_flask)
            self.server_process.start()

    def stop_server(self):
        if self.server_process is not None:
            self.server_process.terminate()
            self.server_process.join()
            self.server_process = None
            self.app = None
            self.auth = None


if __name__ == '__main__':
    try:
        DbAdapter.init('gpucontrol.db')
        server = Server()
        server.run_flask()
        while True:
            sleep(10)
            pass
    except KeyboardInterrupt:
        adapter = DbAdapter.get_adapter()
        adapter.close()
        exit(0)
