import os
import win32event
import win32service
import win32serviceutil

from server import Server
from monitor import Monitor
from modules.db.db_adapter import DbAdapter


class Service(win32serviceutil.ServiceFramework):
    _svc_name_ = "GpuControl"
    _svc_display_name_ = "GPU Usage Control"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

    def SvcDoRun(self):
        DbAdapter.init(os.path.dirname(os.path.abspath(__file__)) + '\\db\\gpucontrol.db')
        monitor = Monitor()
        monitor.start()
        server = Server(monitor=monitor)
        server.run_server()
        win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)

    def SvcStop(self):
        adapter = DbAdapter.get_adapter()
        adapter.close()
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(Service)
