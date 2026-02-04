from pynvml import *
import psutil

class System:
    def __init__(self):
        nvmlInit()
        self.handle = nvmlDeviceGetHandleByIndex(0)
        pass

    def get_gpu_processes(self):
        procs = nvmlDeviceGetComputeRunningProcesses(self.handle)
        result = []

        for p in procs:
            result.append({
                "pid": p.pid,
                "gpu_mem": p.usedGpuMemory
            })
        return result

    def get_working_app_titles(self):
        pids = self.get_working_app_pids()
        titles = {}
        for pid in pids:
            p = psutil.Process(pid)
            if p is not None:
                titles[pid] = p.name()
        return titles

    def get_working_app_pids(self):
        processes = self.get_gpu_processes()
        pids = []
        for p in processes:
            pids.append(p['pid'])
        return pids

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
