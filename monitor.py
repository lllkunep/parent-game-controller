import configparser
import re
from datetime import datetime

class Monitor:
    def get_mem_mb(self):
        match = re.fullmatch(r'(\d+)([A-Za-z])', self.config["Settings"]["gpu_mem_th"])
        if match is None:
            raise TypeError('invalid arg "gpu_mem_th"')

        number = int(match.group(1))
        unit = match.group(2)

        if unit == 'G':
            mem_mb = number * 1024
        elif unit == 'M':
            mem_mb = number
        else:
            raise TypeError('invalid type ' + unit + ' for "gpu_mem_th"')

        return mem_mb

    def get_limit_mins(self):
        limit = self.config["Settings"]["usage_limit"]
        try:
            t = datetime.strptime(limit, "%H:%M")
            total_minutes = t.hour * 60 + t.minute
        except:
            raise ValueError('invalid value ' + limit + ' for "usage_limit"')

        return total_minutes

    def get_time_limits(self):
        try:
            time_deltas = []
            deltas = self.config["Settings"]["time_limits"].split(',')
            for delta in deltas:
                start_end = delta.split('-')
                start = datetime.strptime(start_end[0], "%H:%M")
                end = datetime.strptime(start_end[1], "%H:%M")
                time_deltas += [[{'hour': start.hour, 'min': start.minute}, {'hour': end.hour, 'min': end.minute}]]

        except:
            raise ValueError('invalid values for "time_limits"')
        return time_deltas

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('conf.ini')

        self.gpu_mem_th = self.get_mem_mb()
        self.usage_limit = self.get_limit_mins()
        self.time_limits = self.get_time_limits()
