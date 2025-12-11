
from pathlib import Path
import sqlite3
import datetime
from sqlite_baseObject import sqlite_baseObject
import hashlib

class sqlite_tournamentEntry(sqlite_baseObject):
    def __init__(self):
        self.setup()

    def is_registered(self, userKey, tournamentKey):
        sql = f"SELECT * FROM `{self.tn}` WHERE `userKey` = ? AND `tournamentKey` = ?;"
        self.cur.execute(sql, [userKey, tournamentKey])
        return self.cur.fetchone() is not None

    def register(self, userKey, tournamentKey):
        """Insert entry (let UNIQUE constraint prevent duplicates)."""
        self.set({"userKey": userKey, "tournamentKey": tournamentKey})
        self.insert()

    def unregister(self, userKey, tournamentKey):
        sql = f"DELETE FROM `{self.tn}` WHERE `userKey` = ? AND `tournamentKey` = ?;"
        self.cur.execute(sql, [userKey, tournamentKey])
        self.conn.commit()

    def get_for_tournament(self, tournamentKey):
        """All users in a given tournament."""
        self.data = []
        sql = f"SELECT * FROM `{self.tn}` WHERE `tournamentKey` = ?;"
        self.cur.execute(sql, [tournamentKey])
        for row in self.cur:
            self.data.append(row)
        return self.data


