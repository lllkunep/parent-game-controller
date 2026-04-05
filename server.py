from flask import Flask, request, Response
from threading import Thread
from api import Api
from flask_httpauth import HTTPBasicAuth
import json
import socket

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

        @self.app.route('/')
        def index():
            return 'GPUControl Server'

        @self.app.route('/api/check_user', methods=['GET', 'POST'])
        def check_user():
            self.api = Api(self.monitor)
            return Response(json.dumps(self.api.start_routes('check_user', request)), content_type='application/json')

        @self.auth.verify_password
        def verify_password(username, password):
            if not Options.has_user():
                return False
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

        self.app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

    def run_discovery(self, port=9999):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', port))
        while True:
            data, addr = sock.recvfrom(1024)
            if data != b'gpucontrol-hello':
                continue
            ip = self.monitor.get_reliable_local_ip()
            name = self.monitor.get_host_name()
            response = json.dumps({'name': name, 'ip': ip}).encode()
            sock.sendto(response, addr)

    def run_server(self):
        if self.server_process is None:
            self.server_process = Thread(target=self.run_flask, daemon=True).start()
            Thread(target=self.run_discovery, daemon=True).start()

if __name__ == '__main__':
    from modules.db.db_adapter import DbAdapter
    from monitor import Monitor

    import os
    from time import sleep

    DbAdapter.init(os.path.dirname(os.path.abspath(__file__)) + '\\db\\gpucontrol.db')
    monitor = Monitor()
    monitor.start()
    server = Server(monitor=monitor)
    server.run_server()
    while True:
        sleep(10)