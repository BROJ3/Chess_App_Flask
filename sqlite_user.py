
from pathlib import Path
import sqlite3
import datetime
from sqlite_baseObject import sqlite_baseObject
import hashlib

class sqlite_user(sqlite_baseObject):
    def __init__(self):
        self.setup()
        self.roles = [{'value':'admin','text':'admin'},{'value':'player','text':'player'}]
    def hashPassword(self,pw):
        pw = pw+'xyz'
        return hashlib.md5(pw.encode('utf-8')).hexdigest()
    def role_list(self):
        rl = []
        for item in self.roles:
            rl.append(item['value'])
        return rl
    
    def verify_new(self):
        self.errors = []
        if len(self.data[0]['userID']) < 3:
            self.errors.append('Please select a userID longer than 3 characters.')
        if len(self.data[0]['country']) != 3:
            self.errors.append("Please input the three-letter country code.")
        if '@' not in self.data[0]['email']:
            self.errors.append('Email must contain @')
        u = sqlite_user()
        u.getByField('email',self.data[0]['email'])
        if len(u.data) > 0:
            self.errors.append(f"Email address is already in use. ({self.data[0]['email']})")
        if len(self.data[0]['password']) < 3:
            self.errors.append('Password should be greater than 3 chars.')
        if self.data[0]['password'] != self.data[0]['password2']:
            self.errors.append('Retyped password must match.')
        self.data[0]['password'] = self.hashPassword(self.data[0]['password'])
        if self.data[0]['role'] not in self.role_list():
            self.errors.append(f"Role must be one of {self.role_list()}")
               
        
        if len(self.errors) == 0:
            return True
        else:
            return False
    def verify_update(self):
        self.errors = []
        #
        if '@' not in self.data[0]['email']:
            self.errors.append('Email must contain @')
        u = sqlite_user()
        u.getByField('email',self.data[0]['email'])
        if len(u.data) > 0 and u.data[0][u.pk] != self.data[0][self.pk]:
            self.errors.append(f"Email address is already in use. ({self.data[0]['email']})")
        
        if 'password2' in self.data[0].keys():
            if len(self.data[0]['password']) < 3:
                self.errors.append('Password should be greater than 3 chars.')
            if self.data[0]['password'] != self.data[0]['password2']:
                self.errors.append('Retyped password must match.')
        
            self.data[0]['password'] = self.hashPassword(self.data[0]['password'])
        
        if self.data[0]['role'] not in self.role_list():
            self.errors.append(f"Role must be one of {self.role_list()}")
        #
        
        
        if len(self.errors) == 0:
            return True
        else:
            return False
    
    def tryLogin(self,un, pw):
        pw = self.hashPassword(pw)
        self.data = []
        sql = f'''SELECT * FROM `{self.tn}` WHERE (`email` = ? OR `userID`=?) AND `password` = ?;'''
        self.cur.execute(sql,[un,un,pw])
        for row in self.cur:
            self.data.append(row)
        if len(self.data) == 1:
            return True
        return False
            