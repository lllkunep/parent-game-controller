import hashlib
import json
from datetime import datetime

from modules.db.base_model import BaseModel

class Process(BaseModel):
    type: str
    process_types = ['unknown', 'game', 'application']

    def set_type(self, process_type):
        if process_type not in self.process_types:
            raise ValueError('invalid process type')
        self.type = process_type
        self.save()

    @staticmethod
    def get_by_id(process_id):
        return Process.get_by_pk(process_id)

    @staticmethod
    def get_unknown_count():
        query, params = Process.select(
            fields=['COUNT(id) as count'],
            where={'type = ?':'unknown'}
        )
        counter = Process.fetchone(query, params)
        if counter is None:
            return 0
        else:
            return counter.count

    @staticmethod
    def get_by_type(process_type='all'):
        if process_type not in Process.process_types + ['all']:
            raise ValueError('invalid process type')

        if process_type != 'all':
            where = {'type = ?':process_type}
        else:
            where = None

        query, params = Process.select(
            fields=['id', 'title', 'path', 'type'],
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
            fields=['type', 'COUNT(id) as count'],
            group_by='type'
        )
        counters = Process.fetchall(query, params)

        counter_array = {
            'all': counter_all,
            'unknown': 0,
            'game': 0,
            'application': 0
        }
        for counter in counters:
            counter_array[counter.type] = counter.count

        return counter_array

    @staticmethod
    def get_game_hash_ids():
        query, params = Process.select(
            fields=['title', 'path'],
            where={'type = ?':'game'}
        )
        _processes = Process.fetchall(query, params)
        ids = {}
        for process in _processes:
            text = process.title + process.path
            text_hash = hash(text.encode("utf-8"))
            ids[text_hash] = process.id
        return ids

    @staticmethod
    def get_registered_apps_hash_ids():
        query, params = Process.select(
            fields=['title', 'path'],
            where={'type': ['unknown', 'game']}
        )
        _processes = Process.fetchall(query, params)
        ids = {}
        for process in _processes:
            text = process.title + process.path
            text_hash = hash(text.encode("utf-8"))
            ids[text_hash] = process.id
        return ids

    @staticmethod
    def add_process(title, path, is_game):
        game = Process.from_dict({
            'title': title,
            'path': path,
            'type': 'game' if is_game else 'unknown'
        })
        game.save()


class ProcessLog(BaseModel):
    @staticmethod
    def get_count_by_time(start_time):
        query, params = ProcessLog.select(
            fields=['COUNT(DISTINCT timestamp) as count'],
            join=[['process', 'process.id = process_log.process_id', []]],
            where={'timestamp >= ?':start_time, 'process.type = ?':'game'}
        )
        counter = ProcessLog.fetchone(query, params)
        if counter is None:
            return 0
        else:
            return int(counter.count)

    @staticmethod
    def get_game_work_time(start_time):
        log_count = ProcessLog.get_count_by_time(start_time)
        log_interval = Options.get_log_interval()
        return int(log_count * log_interval / 60)

    @staticmethod
    def get_statistics(process_type='all', start_time=None, end_time=None):
        if process_type not in Process.process_types + ['all']:
            raise ValueError('invalid process type')

        where = {}

        if start_time is not None:
            where['timestamp >= ?'] = start_time
        if end_time is not None:
            where['timestamp <= ?'] = end_time
        if process_type != 'all':
            where['process.type = ?'] = process_type

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

        if len(processes) == 0:
            return []
        query, params = Process.select(where={'id': process_ids})
        process_list = Process.fetchall_by_pk(query, params)

        by_apps = {}
        for app in processes:
            try:
                by_apps[app[0]]['working_time'].append(app[1])
            except KeyError:
                by_apps[app[0]] = {
                    'title': process_list[app[0]].title,
                    'path': process_list[app[0]].path,
                    'process_id': process_list[app[0]].id,
                    'type': process_list[app[0]].type,
                    'total_time': time_sum[app[0]],
                    'working_time': [app[1]]
                }

        return list(by_apps.values())

    @staticmethod
    def add_log(process_id, timestamp):
        ProcessLog.insert({'process_id':process_id, 'timestamp':timestamp})

class Keywords(BaseModel):
    @staticmethod
    def get_all_list():
        _keywords = Keywords.fetchall()
        keywords = []
        for keyword in _keywords:
            keywords.append(keyword.keyword)
        return keywords

    @staticmethod
    def get_by_keyword(keyword):
        query, params = Keywords.select(where={'keyword = ?':keyword})
        return Keywords.fetchone(query, params)

    @staticmethod
    def add_keyword(keyword):
        keywords = Keywords.get_by_keyword(keyword)
        if keywords is None:
            Keywords.insert({'keyword':keyword})
        else:
            raise ValueError('keyword already exists')

    @staticmethod
    def delete_keyword(keyword):
        keywords = Keywords.get_by_keyword(keyword)
        if keywords is not None:
            keywords.delete()
        else:
            raise ValueError('invalid keyword')

class Options(BaseModel):
    allowed_modes = ['auto', 'allow', 'deny']

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

    @staticmethod
    def get_all_list():
        _options = Options.fetchall()
        options = {}
        for option in _options:
            if option.name in ['username', 'password']:
                continue
            if option.name == 'time_limits':
                options[option.name] = []
                limits = option.value.split(',')
                for limit in limits:
                    start_end = limit.split('-')
                    options[option.name].append({'start_time':start_end[0], 'end_time':start_end[1]})
            else:
                options[option.name] = option.value
        return options

    @staticmethod
    def check_password(password):
        return Options.get('password') == hashlib.sha256(password.encode("utf-8")).hexdigest()

    @staticmethod
    def check_username(username):
        return Options.get('username') == username

    @staticmethod
    def update_option(name, value):
        _value = None
        if name == 'username':
            _value = value
        elif name == 'mode':
            if value not in Options.allowed_modes:
                raise ValueError('invalid mode')
            _value = value
        elif name in ['starting_point', 'usage_limit']:
            try:
                datetime.strptime(value, "%H:%M")
                _value = value
            except:
                raise ValueError(f'invalid format for "{name}", must be "HH:MM"')
        elif name in ['log_interval']:
            try:
                _value = int(value)
            except:
                raise ValueError(f'invalid format for "{name}", must be integer')
        elif name in ['time_limits']:
            try:
                _value = json.loads(value)
            except:
                raise ValueError(f'invalid format for "{name}", must be json')
            if not isinstance(_value, list):
                raise ValueError(f'invalid format for "{name}", must be list')
            for limit in _value:
                if not isinstance(limit, dict):
                    raise ValueError(f'invalid format for "{name}", must be list of dicts')
                if 'start_time' not in limit or 'end_time' not in limit:
                    raise ValueError(f'invalid format for "{name}", must be list of dicts with "start_time" and "end_time"')
                try:
                    datetime.strptime(limit['start_time'], "%H:%M")
                    datetime.strptime(limit['end_time'], "%H:%M")
                except:
                    raise ValueError(f'invalid format for "{name}", must be list of dicts with "start_time" and "end_time" in "HH:MM" format')
            for limit in _value:
                if limit['start_time'] > limit['end_time']:
                    raise ValueError(f'invalid format for "{name}", must be list of dicts with "start_time" <= "end_time"')
            _value = ','.join([f'{limit["start_time"]}-{limit["end_time"]}' for limit in _value])
        elif name == 'password':
                try:
                    _value = json.loads(value)
                except:
                    raise ValueError(f'invalid format for "{name}", must be json')
                if not isinstance(_value, dict):
                    raise ValueError(f'invalid format for "{name}", must be json')
                try:
                    old_password = _value['old_password']
                    new_password = _value['new_password']
                except KeyError:
                    raise ValueError(f'invalid format for "{name}", must be object with "old_password" and "new_password"')
                if not Options.check_password(old_password):
                    raise ValueError('invalid old password')
                _value = hashlib.sha256(new_password.encode("utf-8")).hexdigest()
        else:
            raise KeyError('invalid option name')
        Options.update(where={'name = ?':name}, data={'value':_value})

    @staticmethod
    def get_starting_point_h_m():
        starting_point = Options.get('starting_point')
        return datetime.strptime(starting_point, "%H:%M").time()

    @staticmethod
    def get_time_limits():
        time_limits = Options.get('time_limits').split(',')
        _time_limits = []
        for limit in time_limits:
            start_end = limit.split('-')

            _time_limits.append({
                'start': datetime.strptime(start_end[0], "%H:%M").time(),
                'end': datetime.strptime(start_end[1], "%H:%M").time(),
            })
        return _time_limits


class Logs(BaseModel):
    @staticmethod
    def get_data_by_page(page=1, l_from=None, l_to=None, limit=20):
        where = {}
        if l_from is not None:
            where['time >= ?'] = l_from
        if l_to is not None:
            where['time <= ?'] = l_to

        query, params = Logs.select(
            fields=['COUNT(id) as count'],
            where=where
        )

        counter = int(Logs.fetchone(query, params).count)

        total_pages = counter // limit + int(counter % limit > 0)

        query, params = Logs.select(
            limit=limit,
            where=where,
            order_by='id DESC',
            offset=(page-1)*limit
        )
        _logs = Logs.fetchall(query, params)
        logs = []
        for log in _logs:
            logs.append(log.get_data())

        return {
            'page': page,
            'total_pages': total_pages,
            'list': logs,
        }

    @staticmethod
    def save_log(context, message):
        Logs.insert({'context':context, 'message':message, 'time':datetime.now()})
