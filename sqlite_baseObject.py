import yaml
from pathlib import Path
import sqlite3


class sqlite_baseObject:
    def setup(self, config_path='config.yml'):
        self.fields = []
        self.data = []
        self.pk = None
        self.errors = []
        self.config_path = config_path

        self.config = yaml.safe_load(Path(self.config_path).read_text())

        class_name = type(self).__name__
        if class_name.startswith("sqlite_"):
            lookup = class_name[len("sqlite_"):]
        else:
            lookup = class_name

        self.tn = self.config['tables'][lookup]

        db_path = self.config['db']['path']
        def dict_factory(cursor, row):
            return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = dict_factory   
        self.cur = self.conn.cursor()

        self.cur.execute("PRAGMA foreign_keys = ON;")

        self.getFields()

    def set(self, d):
        self.data = [d]

    def getFields(self):

        self.fields = []
        self.pk = None

        sql = f"PRAGMA table_info({self.tn});"
        self.cur.execute(sql)
        for row in self.cur:
            col_name = row["name"]
            is_pk = row["pk"]  
            if is_pk == 1:
                self.pk = col_name
            else:
                self.fields.append(col_name)

    def insert(self, n=0):
        sql = f'INSERT INTO {self.tn} ('
        vals = ''
        tokens = []

        for field in self.fields:
            if field in self.data[n].keys():
                tokens.append(self.data[n][field])
                sql += f'{field}, '
                vals += '?, '

        sql = sql[:-2]  
        vals = vals[:-2]
        sql += f') VALUES ({vals});'

        self.cur.execute(sql, tokens)
        self.conn.commit()
        if self.pk is not None:
            self.data[n][self.pk] = self.cur.lastrowid

    def update(self, n=0):
        sql = f'UPDATE {self.tn} SET '
        parameters = []

        for field in self.fields:
            if field in self.data[n].keys():
                sql += f'{field} = ?,'
                parameters.append(self.data[n][field])

        sql = sql[:-1] 
        sql += f' WHERE {self.pk} = ?;'
        parameters.append(self.data[n][self.pk])

        self.cur.execute(sql, parameters)
        self.conn.commit()

    def getAll(self, order=''):
        self.data = []
        sql = f'SELECT * FROM {self.tn}'
        if order:
            sql += f' ORDER BY {order};'
        else:
            sql += ';'

        self.cur.execute(sql)
        for row in self.cur:
            self.data.append(dict(row))

    def getById(self, id_val):
        self.data = []
        sql = f'SELECT * FROM {self.tn} WHERE {self.pk} = ?;'
        self.cur.execute(sql, [id_val])
        for row in self.cur:
            self.data.append(dict(row))

    def getByField(self, fieldname, value):
        self.data = []
        sql = f'SELECT * FROM {self.tn} WHERE {fieldname} = ?;'
        self.cur.execute(sql, [value])
        for row in self.cur:
            self.data.append(dict(row))

    def deleteById(self, id_val):
        sql = f'DELETE FROM {self.tn} WHERE {self.pk} = ?;'
        self.cur.execute(sql, [id_val])
        self.conn.commit()

    def truncate(self):
        sql = f'DELETE FROM {self.tn};'
        self.cur.execute(sql)
        self.conn.commit()

    def createBlank(self):
        d = {}
        for field in self.fields:
            d[field] = ''
        self.set(d)
