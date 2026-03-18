from flask import Flask, redirect, request
from multiprocessing import Process
from time import sleep
from db import Database
from flask_httpauth import HTTPBasicAuth
import hashlib


class Server:
    def __init__(self, db_path):
        self.server_process = None
        self.is_running = False
        self.app = None
        self.auth = None
        self.processes = []
        self.to_toggle = []
        self.server_process = None
        self.db_path = db_path
        self.db = None
        self.auth_data = {
            'admin': 'admin',
            'password': 'REMOVED',
        }

    def run_flask(self):
        self.app = Flask(__name__)
        self.auth = HTTPBasicAuth()

        @self.auth.verify_password
        def verify_password(username, password):
            passwd = hashlib.sha256(password.encode("utf-8")).hexdigest()
            if username == self.auth_data['admin'] and passwd == self.auth_data['password']:
                return username

        @self.app.route('/processes', methods=['GET', 'POST'])
        @self.auth.login_required
        def processes():
            self.db = Database(self.db_path)
            resp = ''
            if request.method == 'GET':
                try:
                    resp += '<html>\n<head></head><body><table>'
                    resp += '<tr><th>ID</th><th>Name</th><th>Path</th><th>Is exception</th><th>Is new</th><th>Actions</th></tr>'
                    for process in self.db.get_all_apps():
                        if process[3] == 1:
                            is_exception = 'checked'
                        else:
                            is_exception = 'not checked'
                        if process[4] == 1:
                            is_new = 'NEW!!!'
                        else:
                            is_new = ''
                        action_link = f'<a href="/toggle?id={process[0]}">Toggle</a>'
                        resp += f'<tr><td>{process[0]}</td><td>{process[1]}</td><td>{process[2]}</td><td>{is_exception}</td><td>{is_new}</td><td>{action_link}</td></tr>'
                    resp += '</table></body></html>\n'
                except Exception as e:
                    print(e)
            self.db.disconnect()
            self.db = None
            return resp

        @self.app.route('/new-processes', methods=['GET', 'POST'])
        @self.auth.login_required
        def new_processes():
            self.db = Database(self.db_path)
            resp = ''
            if request.method == 'GET':
                try:
                    resp += '<html>\n<head></head><body>'
                    resp += '<a href="/unset-new">Unset new</a>'
                    resp += '<table>'
                    resp += '<tr><th>ID</th><th>Name</th><th>Path</th><th>Is exception</th><th>Is new</th><th>Actions</th></tr>'
                    for process in self.db.get_new_apps():
                        if process[3] == 1:
                            is_exception = 'checked'
                        else:
                            is_exception = 'not checked'
                        if process[4] == 1:
                            is_new = 'NEW!!!'
                        else:
                            is_new = ''
                        action_link = f'<a href="/toggle?id={process[0]}">Toggle</a>'
                        resp += f'<tr><td>{process[0]}</td><td>{process[1]}</td><td>{process[2]}</td><td>{is_exception}</td><td>{is_new}</td><td>{action_link}</td></tr>'
                    resp += '</table></body></html>\n'
                except Exception as e:
                    print(e)
            self.db.disconnect()
            self.db = None
            return resp

        @self.app.route('/unset-new', methods=['GET', 'POST'])
        @self.auth.login_required
        def unset_new():
            self.db = Database(self.db_path)
            if request.method == 'GET':
                self.db.check_new_apps()
            return redirect('/processes')

        @self.app.route('/toggle', methods=['GET', 'POST'])
        @self.auth.login_required
        def toggle():
            self.db = Database(self.db_path)
            if request.method == 'GET':
                process_id = request.args.get('id')
                process = self.db.get_process_by_id(process_id)
                print(process)
                if process[2] == 1:
                    self.db.unset_exception(process_id)
                elif process[2] == 0:
                    self.db.set_exception(process_id)
                self.to_toggle.append(process_id)
                self.db.disconnect()
                self.db = None
            return redirect('/processes')

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
    server = Server()
    server.run_flask()
    while True:
        sleep(10)
        pass
