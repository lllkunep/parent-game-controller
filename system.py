from pynvml import *
import psutil

class System:
    def __init__(self):
        # nvmlInit()
        # self.handle = nvmlDeviceGetHandleByIndex(0)
        pass

    def get_gpu_processes(self):
        # procs = nvmlDeviceGetComputeRunningProcesses(self.handle)
        procs = {}
        result = []

        for p in procs:
            result.append({
                "pid": p.pid,
                "gpu_mem": p.usedGpuMemory
            })
        return result

    def get_working_app_titles(self):
        titles = {}
        return titles

    def get_working_app_pids(self):
        pids = []
        return pids

    def kill_processes(self, titles):
        pids = self.get_working_app_pids()
        for pid in pids:
            p = psutil.Process(pid)
            if p is not None and p.name() in titles:
                psutil.Process(pid).kill()
