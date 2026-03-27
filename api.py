from db import Database


class Api:
    def __init__(self, db_wrapper):
        self.db = db_wrapper
        pass

    def start_routes(self, route, request):
        action = getattr(self, route)
        action(request)
        pass

    def data(self, request):

        pass

    def summary(self, request):
        pass

    def processes(self, request):
        pass

    def statistics(self, request):
        pass

    def options(self, request):
        pass

    def log(self, request):
        pass

    def keywords(self, request):
        pass
