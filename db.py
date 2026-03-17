import sqlite3

class Database:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS `process` (
`id` INTEGER PRIMARY KEY,
`title` TEXT NOT NULL,
`path` TEXT NULL DEFAULT NULL,
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

        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS `keywords`(
`id` INTEGER PRIMARY KEY,
`keyword` text NOT NULL
)
                            ''')

        self.cursor.execute('''
CREATE TABLE IF NOT EXISTS `logs`(
`id` INTEGER PRIMARY KEY,
`context` text NOT NULL,
`message` text NOT NULL
)
                                    ''')

        self.conn.commit()

    def get_process_by_title(self, title):
        self.cursor.execute('SELECT id, title, path, is_exception FROM process WHERE title = ?', (title,))
        data = self.cursor.fetchall()
        if len(data) > 0:
            return data[0]
        else:
            return None

    def save_process(self, title, path, is_exception = False):
        process = self.get_process_by_title(title)
        if process is None:
            self.cursor.execute('INSERT INTO process (title, path, is_exception) VALUES (?, ?, ?)', (title, path, is_exception))
            self.conn.commit()
        elif process[2] != path:
            self.cursor.execute('UPDATE process SET path = ? WHERE id = ?', (path, process[0]))

    def get_process_by_id(self, process_id):
        self.cursor.execute('SELECT id, title, is_exception FROM process WHERE id = ?', (process_id,))
        return self.cursor.fetchone()

    def set_exception(self, process_id):
        self.cursor.execute('UPDATE process SET is_exception = 1 WHERE id = ?', (process_id,))
        self.conn.commit()

    def unset_exception(self, process_id):
        self.cursor.execute('UPDATE process SET is_exception = 0 WHERE id = ?', (process_id,))
        self.conn.commit()

    def save_process_log(self, process_id, timestamp):
        self.cursor.execute('INSERT INTO process_log (process_id, timestamp) VALUES (?, ?)', (process_id, timestamp))
        self.conn.commit()

    def get_process_id_by_title(self, title):
        self.cursor.execute('SELECT id FROM process where title = ?', (title,))
        data = self.cursor.fetchone()
        if data is not None:
            return data[0]
        else:
            return None

    def get_log_count_by_time(self, time):
        self.cursor.execute('SELECT COUNT(DISTINCT timestamp) FROM process_log LEFT JOIN process ON process.id = process_log.process_id WHERE process.is_exception = 0 AND `timestamp` >= ?', (time,))
        data = self.cursor.fetchone()
        if data is not None:
            return data[0]
        else:
            return None

    def get_registered_apps(self):
        self.cursor.execute('SELECT id, title FROM process')
        titles = {}
        for row in self.cursor.fetchall():
            titles[row[0]] = row[1]
        return titles

    def get_all_apps(self):
        self.cursor.execute('SELECT id, title, path, is_exception FROM process')
        return self.cursor.fetchall()

    def get_active_registered_apps(self):
        self.cursor.execute('SELECT title FROM process WHERE is_exception = 0')
        titles = []
        for row in self.cursor.fetchall():
            titles.append(row[0])
        return titles

    def disconnect(self):
        self.conn.commit()
        self.conn.close()

    def get_keywords(self):
        self.cursor.execute('SELECT keyword FROM keywords')
        keywords = []
        for row in self.cursor.fetchall():
            keywords.append(row[0])
        return keywords

    def add_keyword(self, keyword):
        self.cursor.execute('INSERT INTO keywords (keyword) VALUES (?)', (keyword,))
        self.conn.commit()

    def add_default_keywords(self, default_keywords):
        keywords = self.get_keywords()
        for keyword in default_keywords:
            if keyword not in keywords:
                self.add_keyword(keyword)

    def save_log(self, context, message):
        self.cursor.execute('INSERT INTO logs (context, message) VALUES (?, ?)', (context, message))
        self.conn.commit()
