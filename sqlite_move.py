
from pathlib import Path
import sqlite3
import datetime
from sqlite_baseObject import sqlite_baseObject
import hashlib

class sqlite_move(sqlite_baseObject):
    def __init__(self):
        self.setup()

    def verify_new(self):
        self.errors = []
        m = self.data[0]

        if len(m.get('move','')) < 1:
            self.errors.append('move notation is required.')

        if m.get('madeBy') not in ['W', 'B']:
            self.errors.append("madeBy must be 'W' or 'B'.")

        # evalAfter is DECIMAL, but we just check it’s numeric-ish
        try:
            float(m.get('evalAfter'))
        except (TypeError, ValueError):
            self.errors.append('evalAfter must be numeric.')

        if m.get('elapsedTime') is not None:
            try:
                et = int(m['elapsedTime'])
                if et < 0:
                    self.errors.append('elapsedTime must be >= 0.')
            except ValueError:
                self.errors.append('elapsedTime must be an integer.')

        if not m.get('gameKey'):
            self.errors.append('gameKey (FK) is required.')

        return len(self.errors) == 0

    def verify_update(self):
        return self.verify_new()

    def add_move(self, gameKey, san, madeBy, eval_after=0.00, elapsed=None):
        self.set({
            "move": san,
            "madeBy": madeBy,
            "evalAfter": eval_after,
            "elapsedTime": elapsed,
            "gameKey": gameKey,
        })
        if self.verify_new():
            self.insert()
