from datetime import datetime

from modules.db.base_model import BaseModel

class Process(BaseModel):
    @classmethod
    def get_new_count(cls):
        query, params = Process.select(
            fields=['COUNT(id) as count'],
            where={'is_new = ?':1}
        )
        counter = cls.fetchone(query, params)
        if counter is None:
            return 0
        else:
            return counter.count

class ProcessLog(BaseModel):
    @classmethod
    def get_count_by_time(cls, start_time):
        query, params = ProcessLog.select(
            fields=['COUNT(DISTINCT timestamp) as count'],
            join=[['process', 'process.id = process_log.process_id', []]],
            where={'timestamp >= ?':start_time, 'process.is_exception = ?':0}
        )
        counter = cls.fetchone(query, params)
        if counter is None:
            return 0
        else:
            return counter.count

class Keyword(BaseModel):
    pass

class Options(BaseModel):
    @classmethod
    def get(cls, name):
        query, params = Options.select(
            fields=['value'],
            where={'name = ?':name}
        )
        option = Options.fetchone(query, params)
        if option is None:
            raise KeyError('invalid option name')
        return option.value

    @classmethod
    def get_start(cls, date=None):
        option = cls.get('starting_point')
        point = datetime.strptime(option, "%H:%M")
        if date is not None:
            date = datetime.strptime(date, "%Y-%m-%d")
        else:
            date = datetime.now()
        return date.replace(hour=point.hour, minute=point.minute)

    @classmethod
    def get_log_interval(cls):
        return int(cls.get('log_interval'))

    @classmethod
    def get_usage_limit_minutes(cls):
        t = datetime.strptime(cls.get('usage_limit'), "%H:%M")
        return t.hour * 60 + t.minute


class Logs(BaseModel):
    pass