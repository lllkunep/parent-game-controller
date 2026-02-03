import configparser
from datetime import datetime
import re

from db import Database
from system import System

import time


class App:
    def __init__(self):
        self.config = configparser.ConfigParser()
        self.config.read('conf.ini')

        self.gpu_mem_th = self._get_mem_mb()
        self.usage_limit = self._get_limit_mins()
        self.time_limits = self._get_time_limits()
        self.log_interval = self._get_log_interval()
        self.starting_point = self._get_starting_point()

        self.db = Database()
        self.system = System()

    def checking_limits(self):
        return self.check_time_limits() or self.check_allows_time_intervals()

    def check_time_limits(self):
        log_count = self.db.get_log_count_by_time(self.starting_point)
        time_worked = (log_count * self.log_interval) / 60
        return time_worked >= self.usage_limit

    def check_allows_time_intervals(self):
        for start_end in self.time_limits:
            if start_end[0] <= datetime.now().time() <= start_end[1]:
                return True
        return False

    def main_thread(self):
        while True:
            start_time = time.time()
            if self.checking_limits():
                self.system.kill_processes()
            self.save_log()
            end_time = time.time()
            execution_time = end_time - start_time
            time.sleep(self.log_interval - execution_time)

    def save_log(self):
        registered_apps = self.db.get_registered_apps()
        working_app_titles = self.system.get_working_app_titles()
        for key, value in registered_apps.items():
            if value in working_app_titles:
                self.db.save_process_log(key, datetime.now())
        for key, value in working_app_titles.items():
            if value not in registered_apps and key >= self.gpu_mem_th:
                self.db.save_process(value)

    def run(self):
        self.main_thread()

    def _get_mem_mb(self):
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

    def _get_limit_mins(self):
        limit = self.config["Settings"]["usage_limit"]
        try:
            t = datetime.strptime(limit, "%H:%M")
            total_minutes = t.hour * 60 + t.minute
        except:
            raise ValueError('invalid value ' + limit + ' for "usage_limit"')

        return total_minutes

    def _get_time_limits(self):
        try:
            time_deltas = []
            deltas = self.config["Settings"]["time_limits"].split(',')
            for delta in deltas:
                start_end = delta.split('-')
                start = datetime.strptime(start_end[0], "%H:%M")
                end = datetime.strptime(start_end[1], "%H:%M")
                time_deltas.append([start, end])

        except:
            raise ValueError('invalid values for "time_limits"')
        return time_deltas

    def _get_log_interval(self):
        try:
            time_interval = int(self.config["Settings"]["log_interval"])
        except:
            raise ValueError('invalid values for "log_interval"')
        return time_interval

    def _get_starting_point(self):
        try:
            starting_point = datetime.strptime(self.config["Settings"]["starting_point"], "%H:%M")
        except:
            raise ValueError('invalid values for "starting_point"')
        return starting_point
