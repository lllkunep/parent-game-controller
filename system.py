import psutil

class System:
    def __init__(self, logger_func = None):
        self.logger_func = logger_func

    def get_working_app_titles(self):
        pids = self.get_working_app_pids()
        titles = {}
        for pid in pids:
            try:
                p = psutil.Process(pid)
                if p is not None:
                    titles[pid] = p.name()
            except Exception as e:
                self.save_log('system', str(e))
        return titles

    def get_working_app_pids(self):
        allowed_pids = []
        for proc in psutil.pids():
            try:
                p = psutil.Process(proc)
                if p is not None:
                    p.exe()
                    allowed_pids.append(proc)
            except psutil.AccessDenied:
                continue
        return allowed_pids

    def kill_processes(self, titles):
        pids = self.get_working_app_pids()
        for pid in pids:
            try:
                p = psutil.Process(pid)
                if p is not None and p.name() in titles:
                    psutil.Process(pid).kill()
            except Exception as e:
                self.save_log('system', str(e))

    def get_process_path(self, pid):
        try:
            p = psutil.Process(pid)
            if p is not None:
                return p.exe()
            else:
                return None
        except psutil.NoSuchProcess as e:
            self.save_log('system', str(e))
            return None

    def save_log(self, context, message):
        if self.logger_func is not None:
            self.logger_func(context, message)
