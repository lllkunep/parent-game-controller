from models import Options, Process, ProcessLog, Logs, Keywords


class Api:
    def __init__(self, monitor):
        self.request = None
        self.monitor = monitor

    def start_routes(self, route, request):
        action = getattr(self, route)
        self.request = request
        return action()

    def check_user(self):
        if self.request.method == 'POST':
            username = self.request.form.get('username')
            password = self.request.form.get('password')
            if username and password:
                Options.create_user(username, password)
                return {'status': 'success'}
            return {'status': 'error', 'message': 'Invalid username or password'}
        is_exists = Options.has_user()
        return {'status': 'ok', 'exists': is_exists}

    def clear_errors(self):
        self.monitor.status = 'ok'
        return {'status': 'success'}

    def data(self):
        name = self.monitor.get_host_name()
        ip = self.monitor.get_reliable_local_ip()
        status = self.monitor.status
        mode = Options.get('mode')
        return {'name': name, 'ip': ip, 'status': status, 'mode': mode}

    def summary(self):
        date = self.request.args.get('date')
        start = Options.get_start(date)
        time_worked = ProcessLog.get_game_work_time(start)
        usage_limit = Options.get_usage_limit_minutes()
        unknown_apps_count = Process.get_unknown_count()
        time_left = usage_limit - time_worked
        if time_left < 0:
            time_left = 0

        return {'game_time': time_worked, 'time_left': time_left, 'unknown_apps_count': unknown_apps_count}

    def processes(self):
        if self.request.method == 'POST':
            process_id = self.request.form.get('id')
            process_type = self.request.form.get('type')
            process = Process.get_by_id(process_id)
            if process is None:
                return {'status': 'error', 'message': 'Invalid process id'}
            try:
                process.set_type(process_type)
                self.monitor.refresh()
            except ValueError as e:
                return {'status': 'error', 'message': str(e)}
            return {'status': 'success'}

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
        if self.request.method == 'POST':
            try:
                name = self.request.form.get('name')
                value = self.request.form.get('value')
                Options.update_option(name, value)
                self.monitor.refresh()
            except (KeyError, ValueError) as e:
                return {'status': 'error', 'message': str(e)}
            return {'status': 'success', 'message': 'Options updated'}

        return Options.get_all_list()

    def logs(self):
        page = self.request.args.get('page', '1')
        l_from = self.request.args.get('from')
        l_to = self.request.args.get('to')
        data = Logs.get_data_by_page(int(page), l_from, l_to)
        return data

    def keywords(self):
        if self.request.method == 'POST':
            action = self.request.form.get('action')
            keyword = self.request.form.get('keyword')
            try:
                if action == 'add':
                    Keywords.add_keyword(keyword)
                    self.monitor.refresh()
                elif action == 'delete':
                    Keywords.delete_keyword(keyword)
                    self.monitor.refresh()
                else:
                    return {'status': 'error', 'message': 'Invalid action'}
            except ValueError as e:
                return {'status': 'error', 'message': str(e)}
            return {'status': 'success', 'message': 'Keywords updated'}

        return {'keywords': Keywords.get_all_list()}
