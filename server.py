from flask import Flask, redirect, request
from multiprocessing import Process

class Server:
    def __init__(self):
        self.server_process = None
        self.is_running = False
        self.app = Flask(__name__)
        self.register_routes()
        self.processes = []
        self.to_toggle = []

    def run_flask(self):
        self.app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

    def run_server(self):
        if not self.is_running:
            self.server_process = Process(target=self.run_flask)
            self.server_process.start()
            self.is_running = True

    def stop_server(self):
        if self.is_running:
            self.server_process.terminate()
            self.server_process.join()
            self.is_running = False

    def register_routes(self):
        @self.app.route('/processes', methods=['GET', 'POST'])
        def processes():
            if request.method == 'GET':
                print('<html>\n<head></head><body><table>')
                print('<tr><th>ID</th><th>Name</th><th>Is exception</th><th>Actions</th></tr>')
                for process in self.db.get_all_apps():
                    if process[2] == 1:
                        is_exception = 'checked'
                    else:
                        is_exception = 'not checked'
                    action_link = f'<a href="/toggle?id={process[0]}">Toggle</a>'
                    print(
                        f'<tr><td>{process[0]}</td><td>{process[1]}</td><td>{is_exception}</td><td>{action_link}</td></tr>')
                print('</table></body></html>\n')

        @self.app.route('/toggle', methods=['GET', 'POST'])
        def process():
            if request.method == 'GET':
                process_id = request.args.get('id')
                self.to_toggle.append(process_id)
                redirect('/processes')


