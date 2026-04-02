import sqlite3
import threading
from pathlib import Path
from queue import Queue
from threading import Thread


class DbTask:
    def __init__(self, query, func, params=()):
        self.query = query
        self.func = func
        self.params = params
        self.result = None
        self.event = threading.Event()
        self.error = None

    def set_result(self, result):
        self.result = result
        self.event.set()

    def set_error(self, error):
        self.error = error
        self.event.set()

    def get(self, timeout=None):
        self.event.wait(timeout)
        if self.error:
            raise self.error
        return self.result


class DbAdapter:
    _instance = None
    _lock = threading.Lock()

    default_keywords = ['GOG Games', 'Steam', 'Roblox', 'Games']
    default_options = {
        'usage_limit': '02:00',
        'time_limits': '00:00-07:00,22:00-23:59',
        'log_interval': '60',
        'starting_point': '07:00',
        'username': 'admin',
        'password': 'REMOVED',
    }

    @classmethod
    def init(cls, db_path):
        with cls._lock:
            if cls._instance is not None:
                raise RuntimeError('DbAdapter already initialized')
            is_new = not Path(db_path).is_file()
            cls._instance = DbAdapter(db_path)
            cls._instance._setup_schema()
            if is_new:
                cls._instance._fill_defaults()
            cls._instance.start()

    @classmethod
    def get_adapter(cls):
        if cls._instance is None:
            raise RuntimeError('DbAdapter not initialized. Call DbAdapter.init() first.')
        return cls._instance

    def __init__(self, db_path):
        self.db_path = db_path
        self.task_queue = Queue()
        self.thread = None

    def _setup_schema(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS `process` (
                `id` INTEGER PRIMARY KEY,
                `title` TEXT NOT NULL,
                `path` TEXT NULL DEFAULT NULL,
                `is_exception` BOOLEAN NOT NULL DEFAULT 0,
                `is_new` BOOLEAN NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS `process_log` (
                `id` INTEGER PRIMARY KEY,
                `process_id` INTEGER NOT NULL,
                `timestamp` TIMESTAMP NOT NULL
            );
            CREATE TABLE IF NOT EXISTS `keywords` (
                `id` INTEGER PRIMARY KEY,
                `keyword` TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS `logs` (
                `id` INTEGER PRIMARY KEY,
                `context` TEXT NOT NULL,
                `message` TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS `options` (
                `id` INTEGER PRIMARY KEY,
                `name` TEXT NOT NULL,
                `value` TEXT NOT NULL
            );
        ''')
        conn.commit()
        conn.close()

    def _fill_defaults(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        for keyword in self.default_keywords:
            cursor.execute('INSERT INTO keywords (keyword) VALUES (?)', (keyword,))
        for name, value in self.default_options.items():
            cursor.execute('INSERT INTO options (name, value) VALUES (?, ?)', (name, value))
        conn.commit()
        conn.close()

    def db_worker(self):
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()

        while True:
            task = self.task_queue.get()
            try:
                if task.func == 'close':
                    connection.close()
                    task.set_result(True)
                    return

                cursor.execute(task.query, task.params)

                match task.func:
                    case 'fetchone':
                        task.set_result(cursor.fetchone())
                    case 'fetchall':
                        task.set_result(cursor.fetchall())
                    case 'exec':
                        connection.commit()
                        task.set_result(cursor.rowcount)
                    case _:
                        raise TypeError('Invalid function type')
            except sqlite3.Error as e:
                task.set_error(Exception(f'SQLite error: {e} query was: {task.query}'))
            except Exception as e:
                task.set_error(e)

    def start(self):
        self.thread = Thread(target=self.db_worker)
        self.thread.start()


    def fetchone(self, query, params=()):
        task = DbTask(query, 'fetchone', params)
        self.task_queue.put(task)
        return task.get()

    def fetchall(self, query, params=()):
        task = DbTask(query, 'fetchall', params)
        self.task_queue.put(task)
        return task.get()

    def exec(self, query, params=()):
        task = DbTask(query, 'exec', params)
        self.task_queue.put(task)
        return task.get()

    def close(self):
        task = DbTask(None, 'close')
        self.task_queue.put(task)
        task.get()