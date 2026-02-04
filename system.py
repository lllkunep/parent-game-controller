import psutil

class System:
    def __init__(self):
        pass

    def get_working_app_titles(self):
        pids = self.get_working_app_pids()
        titles = {}
        for pid in pids:
            p = psutil.Process(pid)
            if p is not None:
                titles[pid] = p.name()
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
            p = psutil.Process(pid)
            if p is not None and p.name() in titles:
                psutil.Process(pid).kill()

    def is_game(self, pid):
        pass

    def get_process_path(self, pid):
        p = psutil.Process(pid)
        if p is not None:
            return p.exe()
        else:
            return None
