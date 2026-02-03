import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect('main.db')
        self.cursor = self.conn.cursor()

    def init_db(self):
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS `process` (
`id` INTEGER PRIMARY KEY,
`title` TEXT NOT NULL,
`is_exception` BOOLEAN NOT NULL DEFAULT 0
)
                       ''')

        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS `process_log`(
`id` INTEGER PRIMARY KEY,
`process_id` INTEGER NOT NULL,
`timestamp` TIMESTAMP NOT NULL
)
                            ''')

        self.conn.commit()

    def save_process(self, title, is_exception = False):
        self.cursor.execute('INSERT INTO process (title, is_exception) VALUES (?, ?)', (title, is_exception))
        self.conn.commit()

    def save_process_log(self, process_id, timestamp):
        self.cursor.execute('INSERT INTO process_log (process_id, timestamp) VALUES (?, ?)', (process_id, timestamp))
        self.conn.commit()

    def get_process_id_by_title(self, title):
        self.cursor.execute('SELECT id FROM process where title = ?', (title,))
        return self.cursor.fetchone()

    def get_log_count_by_time(self, time):
        self.cursor.execute('SELECT COUNT(DISTINCT timestamp) FROM process_log WHERE `timestamp` >= ?', (time,))
        return self.cursor.fetchone()

    def get_registered_apps(self):
        self.cursor.execute('SELECT id, title FROM process')
        titles = {}
        for row in self.cursor.fetchall():
            titles[row[0]] = row[1]
        return titles

    def disconnect(self):
        self.conn.commit()
        self.conn.close()
