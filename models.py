from datetime import datetime

from modules.db.base_model import BaseModel

class Process(BaseModel):
    process_types = ['all', 'games', 'new', 'not_games']

    @staticmethod
    def get_new_count():
        query, params = Process.select(
            fields=['COUNT(id) as count'],
            where={'is_new = ?':1}
        )
        counter = Process.fetchone(query, params)
        if counter is None:
            return 0
        else:
            return counter.count

    @staticmethod
    def get_by_type(process_type='all'):
        if process_type not in Process.process_types:
            raise ValueError('invalid process type')

        if process_type == 'not_games':
            where = {'is_exception = ?':1}
        elif process_type == 'games':
            where = {'is_exception = ?':0}
        elif process_type == 'new':
            where = {'is_new = ?':1}
        else:
            where = None

        query, params = Process.select(
            fields=['id', 'title', 'path', 'is_exception', 'is_new'],
            where=where
        )
        _processes = Process.fetchall(query, params)
        processes = []
        for process in _processes:
            processes.append(process.get_data())

        return processes

    @staticmethod
    def get_counters():
        query, params = Process.select(fields=['COUNT(id) as count'])
        counter_all = Process.fetchone(query, params).count

        query, params = Process.select(
            fields=['COUNT(id) as count', 'is_exception', 'is_new'],
            group_by='is_exception, is_new'
        )
        counters = Process.fetchall(query, params)

        counter_array = {
            'all': counter_all,
            'games': 0,
            'new': 0,
            'not_games': 0
        }
        for counter in counters:
            if counter.is_exception == 1 and counter.is_new == 0:
                counter_array['not_games'] = counter.count
            elif counter.is_exception == 0 and counter.is_new == 0:
                counter_array['games'] = counter.count
            elif counter.is_exception == 0 and counter.is_new == 1:
                counter_array['new'] = counter.count

        return counter_array


class ProcessLog(BaseModel):
    @staticmethod
    def get_count_by_time(start_time):
        query, params = ProcessLog.select(
            fields=['COUNT(DISTINCT timestamp) as count'],
            join=[['process', 'process.id = process_log.process_id', []]],
            where={'timestamp >= ?':start_time, 'process.is_exception = ?':0}
        )
        counter = ProcessLog.fetchone(query, params)
        if counter is None:
            return 0
        else:
            return counter.count

    @staticmethod
    def get_statistics(process_type='all', start_time=None, end_time=None):
        where = {}

        if start_time is not None:
            where['timestamp >= ?'] = start_time
        if end_time is not None:
            where['timestamp <= ?'] = end_time
        if process_type == 'games':
            where['process.is_exception = ?'] = 0
        elif process_type == 'new':
            where['process.is_new = ?'] = 1
        elif process_type == 'all':
            pass
        else:
            raise ValueError('invalid process type')

        query, params = ProcessLog.select(
            fields=['process_log.id', 'process_log.`timestamp`', 'process_log.process_id'],
            join=[['process', 'process.id = process_log.process_id', []]],
            where=where,
            order_by='process_log.`timestamp`'
        )

        statistics = ProcessLog.fetchall(query, params)

        log_interval = Options.get_log_interval()

        group_by_time = {}
        process_ids = []
        for stat in statistics:
            if stat.process_id not in process_ids:
                process_ids.append(stat.process_id)
            try:
                group_by_time[stat.timestamp].append(stat)
            except KeyError:
                group_by_time[stat.timestamp] = [stat]

        processes = []
        current_processes = {}
        time_sum = {}
        for time, stats in group_by_time.items():
            opened_processes = []
            for stat in stats:
                try:
                    time_sum[stat.process_id] += (log_interval / 60)
                except KeyError:
                    time_sum[stat.process_id] = (log_interval / 60)
                opened_processes.append(stat.process_id)
                try:
                    current_processes[stat.process_id]['end_time'] = stat.timestamp
                except KeyError:
                    current_processes[stat.process_id] = {'start_time': stat.timestamp, 'end_time': stat.timestamp}

            to_delete = []
            for current_process in current_processes.keys():
                if current_process not in opened_processes:
                    processes.append([current_process, current_processes[current_process]])
                    to_delete.append(current_process)

            for current_process in to_delete:
                del current_processes[current_process]

        for process_id, current_process in current_processes.items():
            processes.append([process_id, current_process])

        query, params = Process.select(where={'id': process_ids})
        process_list = Process.fetchall_by_pk(query, params)

        by_apps = {}
        for app in processes:
            try:
                by_apps[app[0]]['times'].append(app[1])
            except KeyError:
                by_apps[app[0]] = {
                    'title': process_list[app[0]].title,
                    'path': process_list[app[0]].path,
                    'process_id': process_list[app[0]].id,
                    'is_exception': process_list[app[0]].is_exception,
                    'is_new': process_list[app[0]].is_exception,
                    'total_time': time_sum[app[0]],
                    'working_time': [app[1]]
                }

        return list(by_apps.values())

class Keyword(BaseModel):
    pass

class Options(BaseModel):
    @staticmethod
    def get(name):
        query, params = Options.select(
            fields=['value'],
            where={'name = ?':name}
        )
        option = Options.fetchone(query, params)
        if option is None:
            raise KeyError('invalid option name')
        return option.value

    @staticmethod
    def get_start(date=None):
        option = Options.get('starting_point')
        point = datetime.strptime(option, "%H:%M")
        if date is not None:
            date = datetime.strptime(date, "%Y-%m-%d")
        else:
            date = datetime.now()
        return date.replace(hour=point.hour, minute=point.minute)

    @staticmethod
    def get_log_interval():
        return int(Options.get('log_interval'))

    @staticmethod
    def get_usage_limit_minutes():
        t = datetime.strptime(Options.get('usage_limit'), "%H:%M")
        return t.hour * 60 + t.minute


class Logs(BaseModel):
    pass