from pynvml import *

class System:
    def __init__(self, gpu_mem_threshold):
        nvmlInit()
        self.handle = nvmlDeviceGetHandleByIndex(0)
        self.gpu_mem_threshold = gpu_mem_threshold
        pass

    def get_gpu_processes(self):
        procs = nvmlDeviceGetComputeRunningProcesses(self.handle)
        result = []

        for p in procs:
            if p.usedGpuMemory >= self.gpu_mem_threshold:
                result.append({
                    "pid": p.pid,
                    "gpu_mem": p.usedGpuMemory
                })

        return result
