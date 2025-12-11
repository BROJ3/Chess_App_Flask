
from pathlib import Path
import sqlite3
import datetime
from sqlite_baseObject import sqlite_baseObject
import hashlib

class sqlite_tournament(sqlite_baseObject):
    def __init__(self):
        self.setup()

    def get_participants(self):
        for field in self.data:
            print(field)
        return 

    def get_info(self):
        for field in self.data:
            print(field)

    def verify_new(self):
        self.errors = []

        t=sqlite_tournament()
        t.getByField('tournamentID', self.data[0]['tournamentID'])
        if len(t.data) > 0:
            self.errors.append("tournament id is already in use.")
        
        if len(self.errors) == 0:
            return True
        else:
            return False
        
    def verify_update(self):
        self.errors = []
        t=sqlite_tournament()
        t.getByField('tournamentID', self.data[0]['tournamentID'])
        if len(t.data) > 0:
            self.errors.append("tournament id is already in use.")
        
        if len(self.errors) == 0:
            return True
        else:
            return False

            