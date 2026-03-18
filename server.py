from datetime import datetime

from flask import Flask, redirect, request
from multiprocessing import Process
from time import sleep
from db import Database
from flask_httpauth import HTTPBasicAuth
import hashlib


class Server:
    def __init__(self, db_path, starting_point, log_interval):
        self.server_process = None
        self.is_running = False
        self.app = None
        self.auth = None
        self.processes = []
        self.to_toggle = []
        self.server_process = None
        self.db_path = db_path
        self.starting_point = starting_point
        self.log_interval = log_interval
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

        @self.app.route('/statistics', methods=['GET', 'POST'])
        @self.auth.login_required
        def statistics():
            self.db = Database(self.db_path)
            # (9, '2026-03-18 21:12:49.963271', 22,  'logioptionsplus_updater.exe','C:\\Program Files\\LogiOptionsPlus\\logioptionsplus_updater.exe', 1, 1)
            if request.method == 'GET':
                today_start = datetime.now()
                today_start = today_start.replace(hour=self.starting_point.hour, minute=self.starting_point.minute)
                stats = self.db.get_statistics(today_start)
                print(today_start)
                group_by_time = {}

                for stat in stats:
                    try:
                        group_by_time[stat[1]].append(stat)
                    except KeyError:
                        group_by_time[stat[1]] = [stat]
                games = []
                not_games = []
                current_games = {}
                current_not_games = {}
                time_sum = {}
                for time, stats in group_by_time.items():
                    opened_games = []
                    opened_not_games = []
                    for stat in stats:
                        try:
                            time_sum[stat[2]] += (self.log_interval / 60)
                        except KeyError:
                            time_sum[stat[2]] = (self.log_interval / 60)
                        if stat[5] == 0:
                            opened_games.append(stat[2])
                            try:
                                current_games[stat[2]]['end_time'] = stat[1]
                            except KeyError:
                                current_games[stat[2]] = {'start_time': stat[1], 'end_time': stat[1]}
                        else:
                            opened_not_games.append(stat[2])
                            try:
                                current_not_games[stat[2]]['end_time'] = stat[1]
                            except KeyError:
                                current_not_games[stat[2]] = {'start_time': stat[1], 'end_time': stat[1]}

                    to_delete = []
                    for current_game in current_games.keys():
                        if current_game not in opened_games:
                            games.append([current_game, current_games[current_game]])
                            to_delete.append(current_game)

                    for current_game in to_delete:
                        del current_games[current_game]

                    to_delete = []
                    for current_not_game in current_not_games.keys():
                        if current_not_game not in opened_not_games:
                            not_games.append([current_not_game, current_not_games[current_not_game]])
                            to_delete.append(current_not_game)
                    for current_not_game in to_delete:
                        del current_not_games[current_not_game]

                for process_id, current_game in current_games.items():
                    games.append([process_id, current_game])

                for process_id, current_not_game in current_not_games.items():
                    not_games.append([process_id, current_not_game])

                registered_apps = self.db.get_registered_apps()
                registered_paths = self.db.get_registered_paths()
                by_games = {}
                for game in games:
                    try:
                        by_games[game[0]]['times'].append(game[1])
                    except KeyError:
                        by_games[game[0]] = {
                            'id': game[0],
                            'title': registered_apps[game[0]],
                            'path': registered_paths[game[0]],
                            'times': [game[1]]
                        }

                by_apps = {}
                for app in not_games:
                    try:
                        by_apps[app[0]]['times'].append(app[1])
                    except KeyError:
                        by_apps[app[0]] = {
                            'id': app[0],
                            'title': registered_apps[app[0]],
                            'path': registered_paths[app[0]],
                            'times': [app[1]]
                        }

                pass
                response = f'<html>\n<head></head><body>'

                response += '<h1>Games</h1>'
                response += '<table>'
                for game in by_games.values():
                    response += '<tr><td><b>' + game['title'] + '</b> : ' + str(int(time_sum[game['id']])) + ' mins</td><td>' + game['path'] + '</td></tr>'
                    for time in game['times']:
                        response += '<tr><td>' + time['start_time'] + '</td><td>' + time['end_time'] + '</td></tr>'
                response += '</table>'

                response += '<h1>Apps</h1>'
                response += '<table>'
                for app in by_apps.values():
                    response += '<tr><td><b>' + app['title'] + '</b> : ' + str(int(time_sum[app['id']])) + ' mins</td><td>' + app['path'] + '</td></tr>'
                    for time in app['times']:
                        response += '<tr><td>' + time['start_time'] + '</td><td>' + time['end_time'] + '</td></tr>'
                response += '</table>'

                response += '</body></html>\n'
                return response

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
