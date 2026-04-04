from models import *
from system import System


class Api:
    def __init__(self):
        self.request = None

    def start_routes(self, route, request):
        action = getattr(self, route)
        self.request = request
        return action()

    def data(self):
        name = System.get_host_name()
        ip = System.get_reliable_local_ip()
        status = 'Ok'
        return {'name': name, 'ip': ip, 'status': status}

    def summary(self):
        date = self.request.args.get('date')
        start = Options.get_start(date)
        log_count = ProcessLog.get_count_by_time(start)
        log_interval = Options.get_log_interval()

        usage_limit = Options.get_usage_limit_minutes()
        time_worked = int((log_count * log_interval) / 60)
        new_apps_count = Process.get_new_count()
        time_left = usage_limit - time_worked
        if time_left < 0:
            time_left = 0

        return {'game_time': log_count, 'time_left': time_left, 'new_apps_count': new_apps_count}

    def processes(self):
        process_type = self.request.args.get('type', 'all')
        processed_apps = Process.get_by_type(process_type)
        counters = Process.get_counters()
        return {'list ': processed_apps, 'counters': counters}

    def statistics(self):
        process_type = self.request.args.get('type', 'all')
        from_time = self.request.args.get('from')
        to_time = self.request.args.get('to')

        p_list = ProcessLog.get_statistics(process_type, from_time, to_time)

        return {'list': p_list}

    def options(self):
        pass

    def log(self):
        pass

    def keywords(self):
        pass
