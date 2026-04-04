import re
from modules.db.db_adapter import DbAdapter


class BaseModel:
    primary_key = None
    table_name = None

    def __init__(self, **kwargs):
        self.__dict__['data'] = {}
        for key, value in kwargs.items():
            self.__dict__['data'][key] = value

    def save(self):
        primary_key = self.get_primary_key()
        if primary_key not in self.data or self.data[primary_key] is None:
            self.insert(self.data)
        else:
            self.update({primary_key: self.data[primary_key]}, self.data)
        return self

    def delete(self):
        table_name = self.get_table_name()
        primary_key = self.get_primary_key()
        query = f'DELETE FROM {table_name}' + f' WHERE {primary_key} = ?'
        adapter = DbAdapter.get_adapter()
        adapter.exec(query, (self.data[primary_key],))

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[name]
        else:
            if name not in self.__dict__['data']:
               raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
            return self.__dict__['data'][name]

    def __setattr__(self, name, value):
        if name in self.__dict__:
            self.__dict__[name] = value
        else:
            self.__dict__['data'][name] = value

    def get_data(self):
        return self.data

    @classmethod
    def get_by_pk(cls, pk):
        query = f'SELECT * FROM {cls.get_table_name()} WHERE {cls.get_primary_key()} = ?'
        adapter = DbAdapter.get_adapter()
        data = adapter.fetchone(query, (pk,))
        if data:
            return cls(**data)
        else:
            return None

    @classmethod
    def get_table_name(cls):
        if cls.table_name is None:
            cls.table_name = cls.camel_to_snake(cls.__name__)
        return cls.table_name

    @classmethod
    def get_primary_key(cls):
        if cls.primary_key is None:
            cls.primary_key = 'id'
        return cls.primary_key

    @classmethod
    def insert(cls, data):
        data = dict(data)
        data.pop(cls.get_primary_key(), None)
        table_name = cls.get_table_name()
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?'] * len(data))
        query = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'
        adapter = DbAdapter.get_adapter()
        adapter.exec(query, tuple(data.values()))

    @classmethod
    def update(cls, where, data):
        pk = cls.get_primary_key()
        table_name = cls.get_table_name()

        set_items = {k: v for k, v in data.items() if k != pk}
        set_clause = ', '.join(f'{k} = ?' for k in set_items)
        where_clause = ' AND '.join(f'{k} = ?' for k in where)

        query = f'UPDATE {table_name} SET {set_clause} WHERE {where_clause}'

        params = tuple(set_items.values()) + tuple(where.values())

        adapter = DbAdapter.get_adapter()
        adapter.exec(query, params)

    @staticmethod
    def camel_to_snake(camel_case_string):
        s1 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', camel_case_string)
        return s1.lower()

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    @classmethod
    def fetchall(cls, query, params=()):
        adapter = DbAdapter.get_adapter()
        data = adapter.fetchall(query, params)
        rows = []
        for row in data:
            rows.append(cls.from_dict(dict(row)))
        return rows

    @classmethod
    def fetchall_by_pk(cls, query, params=()):
        adapter = DbAdapter.get_adapter()
        data = adapter.fetchall(query, params)
        rows = {}
        for row in data:
            rows[row[cls.get_primary_key()]] = cls.from_dict(dict(row))
        return rows

    @classmethod
    def fetchone(cls, query, params=()):
        adapter = DbAdapter.get_adapter()
        data = adapter.fetchone(query, params)
        if data:
            return cls.from_dict(dict(data))
        else:
            return None

    @classmethod
    def select(cls, fields=None, where=None, join=None, order_by=None, limit=None, offset=None, group_by=None):
        if fields is None:
            fields = [f'{cls.get_table_name()}.*']
        select_clause = ', '.join(fields)

        join_clause = ''
        if join:
            for table, on, join_fields in join:
                if join_fields:
                    select_clause += ', ' + ', '.join(f'{table}.{f}' for f in join_fields)
                join_clause += f' LEFT JOIN {table} ON {on}'

        params = []
        where_clause = ''
        if where:
            conditions = []
            for condition, value in where.items():
                if isinstance(value, (list, tuple)):
                    placeholders = ', '.join(['?'] * len(value))
                    conditions.append(f'{condition} IN ({placeholders})')
                    params.extend(value)
                else:
                    conditions.append(condition)
                    params.append(value)
            where_clause = ' WHERE ' + ' AND '.join(conditions)
            params = tuple(params)

        query = f'SELECT {select_clause} FROM {cls.get_table_name()}{join_clause}{where_clause}'

        if order_by:
            query += f' ORDER BY {order_by}'
        if group_by:
            query += f' GROUP BY {group_by}'
        if limit:
            query += f' LIMIT {limit}'
        if offset:
            query += f' OFFSET {offset}'

        return query, params

    def __repr__(self):
        return f'<{self.__class__.__name__} {self.data}>'
