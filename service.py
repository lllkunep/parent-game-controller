import win32event
import win32service
import win32serviceutil
from time import sleep

from server import Server
from monitor import Monitor
from modules.db.db_adapter import DbAdapter


class Service(win32serviceutil.ServiceFramework):
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)

    def SvcDoRun(self):
        DbAdapter.init('db/gpucontrol.db')
        monitor = Monitor()
        monitor.start()
        server = Server(monitor=monitor)
        server.run_server()
        while True:
            sleep(10)

    def SvcStop(self):
        adapter = DbAdapter.get_adapter()
        adapter.close()
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        exit(0)


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(Service)
