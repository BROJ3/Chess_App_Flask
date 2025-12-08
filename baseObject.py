import yaml
from pathlib import Path
import pymysql
import datetime

class baseObject:
    def setup(self,config_path = 'config.yml'):
        self.fields = []
        self.data = []
        self.pk = None
        self.errors = []
        self.config_path = config_path
        self.config = yaml.safe_load(Path(self.config_path).read_text())
        self.tn = self.config['tables'][type(self).__name__]
        #print(self.config)
        self.conn = pymysql.connect(host=self.config['db']['host'], 
                                    port=3306, 
                                    user=self.config['db']['user'],
                                    passwd=self.config['db']['pw'], 
                                    db=self.config['db']['db'], 
                                    autocommit=True)


        
        self.cur = self.conn.cursor(pymysql.cursors.DictCursor)
        self.getFields()

    def set(self,d):
        self.data = []
        self.data.append(d)

    def getFields(self):
        self.fields = []
        sql = f"DESC `{self.tn}`"
        self.cur.execute(sql)
        for row in self.cur:
            if row['Extra'] == 'auto_increment':
                self.pk = row['Field']
            else:
                self.fields.append(row['Field'])
        #print(self.fields)


    def insert(self,n=0):
        sql = f'INSERT INTO `{self.tn}` ('
        vals = ''
        tokens = []
        for field in self.fields:
            if field in self.data[n].keys():
                tokens.append(self.data[n][field])
                sql += f'`{field}`,' + ' '
                vals += '%s, '
        sql = sql[0:-2]
        vals = vals[0:-2]
        sql += ') VALUES '
        sql += f'({vals});'
        #print(sql,tokens)
        self.cur.execute(sql,tokens)
        self.data[n][self.pk] = self.cur.lastrowid
    def update(self,n=0):
        sql = f'UPDATE `{self.tn}` SET '
        parameters = []   
        n=0
        for field in self.fields:
            if field in self.data[n].keys():
                sql += f'`{field}` = %s,' 
                parameters.append(self.data[n][field])
        sql = sql[0:-1]
        sql += f' WHERE `{self.pk}` = %s;'
        parameters.append(self.data[0][self.pk])
        #print(sql,parameters)
        self.cur.execute(sql, parameters)
    
   
    def getAll(self,order=''):
        self.data = []
        sql = f'''SELECT * FROM `{self.tn}`'''
        if order != '':
            sql += f' ORDER BY {order};'
        else:
            sql += ';'
        self.cur.execute(sql)
        for row in self.cur:
            self.data.append(row)
    def getById(self,id):
        self.data = []
        sql = f'''SELECT * FROM `{self.tn}` WHERE `{self.pk}` = %s;'''
        self.cur.execute(sql,[id])
        for row in self.cur:
            self.data.append(row)
    def getByField(self,fieldname, value):
        self.data = []
        sql = f'''SELECT * FROM `{self.tn}` WHERE `{fieldname}` = %s;'''
        self.cur.execute(sql,[value])
        for row in self.cur:
            self.data.append(row)
    def deleteById(self,id):
        sql = f'''DELETE FROM `{self.tn}` WHERE `{self.pk}` = %s;'''
        self.cur.execute(sql,[id])
    def truncate(self):
        sql = f'''TRUNCATE TABLE `{self.tn}`;'''
        self.cur.execute(sql)
    def createBlank(self):
        d = {}
        for field in self.fields:
            d[field] = ''
        self.set(d)