from threading import Thread
from time import time, sleep
import psutil
import socket
from datetime import datetime

from models import Process, ProcessLog, Logs, Keywords, Options

class Monitor:
    system_app_path = 'C:\\Windows'

    def __init__(self):
        self.configs = {}
        self._refresh = True
        self.running_processes = {}
        self.monitor_thread = None
        self.working_apps = None
        self.status = 'ok'
        self.mode = None
        self.log_time = datetime.now()

    def start(self):
        self.monitor_thread = Thread(target=self.main_loop, daemon=True)
        self.monitor_thread.start()

    def main_loop(self):
        while True:
            try:
                start_time = time()
                self.log_time = datetime.now()
                if self._refresh:
                    self.read_configs()
                self.working_apps = self._get_working_apps()
                if self.mode == 'auto':
                    if self._checking_limits():
                        self._kill_games()
                elif self.mode == 'deny':
                    self._kill_games()
                self._write_log()
                end_time = time()
                execution_time = end_time - start_time
                sleep(max(0, self.configs['log_interval'] - execution_time))
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except Exception as e:
                self.status = 'has-error'
                Logs.save_log('monitor', str(e))

    def refresh(self):
        self._refresh = True

    def read_configs(self):
        self.configs = {
            'log_interval': Options.get_log_interval(), 'starting_point': Options.get_starting_point_h_m(),
            'usage_limit': Options.get_usage_limit_minutes(), 'time_limits': Options.get_time_limits(),
            'games_hashes': Process.get_game_hash_ids(), 'logging_hashes': Process.get_for_logging_hash_ids(), 'all_apps_hashes': Process.get_registered_apps_hash_ids(), 'keywords': Keywords.get_all_list(),
        }
        self.mode = Options.get('mode')
        self._refresh = False

    def _checking_limits(self):
        today_start = datetime.now()
        today_start = today_start.replace(hour=self.configs['starting_point'].hour, minute=self.configs['starting_point'].minute, second=0, microsecond=0)
        time_worked = ProcessLog.get_game_work_time(today_start)
        if time_worked >= self.configs['usage_limit']:
            return True

        for time_limit in self.configs['time_limits']:
            if time_limit['start'] <= datetime.now().time() <= time_limit['end']:
                return True

        return False

    def _write_log(self):
        process_ids_logs = []
        for pid, app in self.working_apps.items():
            text = app["title"] + app["path"]
            text_hash = hash(text.encode("utf-8"))
            if text_hash not in self.configs['all_apps_hashes'].keys():
                is_game = False
                for keyword in self.configs['keywords']:
                    if keyword in app['path']:
                        is_game = True
                        break
                Process.add_process(app['title'], app['path'], is_game)
                self.configs['games_hashes'] = Process.get_game_hash_ids()
                self.configs['logging_hashes'] = Process.get_for_logging_hash_ids()
                self.configs['all_apps_hashes'] = Process.get_registered_apps_hash_ids()
            try:
                if text_hash in self.configs['logging_hashes'].keys():
                    if self.configs['all_apps_hashes'][text_hash] not in process_ids_logs:
                        process_ids_logs.append(self.configs['all_apps_hashes'][text_hash])
            except KeyError:
                pass
        for p_id in process_ids_logs:
            ProcessLog.add_log(p_id, self.log_time)

    def _kill_games(self):
        for text_hash, pid in self.running_processes.items():
            if text_hash in self.configs['games_hashes'].keys():
                psutil.Process(pid).kill()

    def _get_working_apps(self):
        self.running_processes = {}
        working_apps = {}
        for proc in psutil.pids():
            try:
                p = psutil.Process(proc)
                name = p.name()
                path = p.exe()
                if path != '' and Monitor.system_app_path not in path:
                    working_apps[proc] = {'title': name, 'path': path}
                    text = name + path
                    text_hash = hash(text.encode("utf-8"))
                    self.running_processes[text_hash] = proc
            except psutil.Error:
                continue
        return working_apps

    @staticmethod
    def get_reliable_local_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('8.8.8.8', 80))
            ip_address = s.getsockname()[0]
        except socket.error:
            ip_address = '127.0.0.1'
        finally:
            s.close()
        return ip_address

    @staticmethod
    def get_host_name():
        return socket.gethostname()
