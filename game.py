from pathlib import Path
import pymysql
import datetime
from baseObject import baseObject
import hashlib
import random
import chess
import chess.pgn
from user import user
from tournament import tournament


class game(baseObject):
    def __init__(self):
        self.setup()
        self.valid_results = ['1-0', '0-1', '0.5-0.5', '*']

    def start_game(self, whiteKey, blackKey, tournamentKey=None, round=None):
        g = game()
        g.set({
            "gameID": str(str(whiteKey) + "match" + str(blackKey) + str(random.randint(1, 200))),
            "result": "*",
            "date": datetime.date.today(),
            "tournamentKey": tournamentKey,
            "whiteKey": whiteKey,
            "blackKey": blackKey,
            "round": round,
        })
        g.insert()
        return g.data[0][g.pk]

    def verify_new(self):
        self.errors = []
        g = self.data[0]

        if len(g.get('gameID','')) < 1:
            self.errors.append('gameID is required.')

        if not g.get('date'):
            self.errors.append('date is required.')

        if g.get('whiteKey') == g.get('blackKey'):
            self.errors.append('White and Black must be different players.')

        if g.get('result') not in self.valid_results:
            self.errors.append(f"result must be one of {self.valid_results}.")

        return len(self.errors) == 0

    def verify_update(self):
        return self.verify_new()

    def build_pgn_and_fens(self, game_row, moves_rows):
            """
            Build a chess.pgn.Game object and list of FENs for a game.

            Fills PGN headers with:
            - Event: tournament name or "Casual Game"
            - Site: tournament location or "online"
            - Date: game date
            - White / Black: userID of players
            - Result: game result
            """
            board = chess.Board()
            game_pgn = chess.pgn.Game()

            event_name = "Casual Game"
            site = "online"

            t_key = game_row.get("tournamentKey")
            if t_key:
                t_obj = tournament()
                t_obj.getById(t_key)
                if t_obj.data:
                    trow = t_obj.data[0]
                    if trow.get("name"):
                        event_name = trow["name"]
                    if trow.get("location"):
                        site = trow["location"]

            u_obj = user()
            white_name = "?"
            black_name = "?"

            w_key = game_row.get("whiteKey")
            if w_key:
                u_obj.getById(w_key)
                if u_obj.data:
                    white_name = u_obj.data[0].get("userID") or white_name

            u_obj.data = [] 
            b_key = game_row.get("blackKey")
            if b_key:
                u_obj.getById(b_key)
                if u_obj.data:
                    black_name = u_obj.data[0].get("userID") or black_name

            game_pgn.headers["Event"] = event_name
            game_pgn.headers["Site"] = site
            game_pgn.headers["Date"] = str(game_row.get("date", "????.??.??"))
            game_pgn.headers["White"] = white_name
            game_pgn.headers["Black"] = black_name
            game_pgn.headers["Result"] = game_row.get("result", "0.5-0.5")

            node = game_pgn
            fens = [board.fen()]

            for mv in moves_rows:
                san = mv["move"]
                move = board.parse_san(san)
                board.push(move)
                fens.append(board.fen())
                node = node.add_variation(move)

            return str(game_pgn), fens
