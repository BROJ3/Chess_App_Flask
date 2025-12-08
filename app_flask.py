from flask import Flask
from flask import render_template
from flask import request,session, redirect, url_for, send_from_directory,make_response, jsonify
from flask_session import Session
from datetime import timedelta
from user import user
import time
from user import user
from tournament import tournament
from tournament_entry import tournamentEntry
from game import game
from move import move
import chess
import chess.pgn
import datetime
import random
from collections import defaultdict


app = Flask(__name__,static_url_path='')

app.config['SECRET_KEY'] = 'sdfvbgfdjeR5y5r'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=5)
sess = Session()
sess.init_app(app)


def maybe_advance_knockout_round(tournamentKey):

    g = game()
    sql_all = f"SELECT * FROM `{g.tn}` WHERE `tournamentKey` = %s AND `round` IS NOT NULL;"
    g.cur.execute(sql_all, [tournamentKey])
    all_games = [row for row in g.cur]

    if not all_games:
        return all_games

    max_round = max(row.get("round", 0) or 0 for row in all_games)
    if max_round <= 0:
        return all_games

    current_round_games = [row for row in all_games if row.get("round") == max_round]

    pairings = defaultdict(list)
    for row in current_round_games:
        wk = row.get("whiteKey")
        bk = row.get("blackKey")
        key = tuple(sorted((wk, bk)))
        pairings[key].append(row)

    winners = []

    for (wk, bk), games in pairings.items():
        decisive = None
        for row in games:
            result = row.get("result")
            if result == "1-0":
                decisive = wk
                break
            elif result == "0-1":
                decisive = bk
                break

        if decisive:
            winners.append(decisive)
            continue  # Next pairing

        # If all games for this pairing are draws → create tiebreak
        all_draws = all(row.get("result") == "0.5-0.5" for row in games)

        if all_draws:
            # Create a new tiebreak game in the same round
            new_game = game()
            # Alternate colors for fairness
            if len(games) % 2 == 0:
                white, black = wk, bk
            else:
                white, black = bk, wk

            new_game.start_game(
                whiteKey=white,
                blackKey=black,
                tournamentKey=tournamentKey,
                round=max_round
            )

            g.cur.execute(sql_all, [tournamentKey])
            return [row for row in g.cur]

        unfinished_exists = any(row.get("result") in ("*", None, "") for row in games)
        if unfinished_exists:
            return all_games

    if len(winners) < 2:
        return all_games

    next_round = max_round + 1


    random.shuffle(winners)  # Optional: randomize seeding

    new_round = game()
    for i in range(0, len(winners), 2):
        white = winners[i]
        black = winners[i + 1]
        new_round.start_game(
            whiteKey=white,
            blackKey=black,
            tournamentKey=tournamentKey,
            round=next_round
        )

    # Reload games and return
    g.cur.execute(sql_all, [tournamentKey])
    return [row for row in g.cur]



def maybe_create_final_for_tournament(tournamentKey):
    """
    If all existing games for this tournament are finished and there are
    at least 2 players, automatically create a final between the top 2
    scorers (if such a final does not already exist).

    Returns the updated list of games for that tournament.
    """
    g = game()

    # Load all games for this tournament
    sql_games = f"SELECT * FROM `{g.tn}` WHERE `tournamentKey` = %s;"
    g.cur.execute(sql_games, [tournamentKey])
    games = [row for row in g.cur]

    if not games:
        # No games yet -> nothing to base a final on
        return games

    # If ANY game is not finished yet, don't create a final
    unfinished = [row for row in games
                  if row.get('result') in (None, '', '*')]
    if unfinished:
        return games

    # --- Compute scores per player (1 = win, 0.5 = draw, 0 = loss) ---
    stats = {}  # userKey -> dict
    def ensure_player(uk):
        if uk is None:
            return
        if uk not in stats:
            stats[uk] = {
                "userKey": uk,
                "points": 0.0,
            }

    for row in games:
        whiteKey = row.get('whiteKey')
        blackKey = row.get('blackKey')
        result = row.get('result')

        ensure_player(whiteKey)
        ensure_player(blackKey)

        if result == '1-0':
            if whiteKey in stats:
                stats[whiteKey]["points"] += 1.0
            if blackKey in stats:
                stats[blackKey]["points"] += 0.0
        elif result == '0-1':
            if blackKey in stats:
                stats[blackKey]["points"] += 1.0
            if whiteKey in stats:
                stats[whiteKey]["points"] += 0.0
        elif result == '0.5-0.5':
            if whiteKey in stats:
                stats[whiteKey]["points"] += 0.5
            if blackKey in stats:
                stats[blackKey]["points"] += 0.5
        # ignore other results

    if len(stats) < 2:
        # Not enough distinct players to make a final
        return games

    # Sort players by score (desc), tie-break by userKey
    standings = sorted(
        stats.values(),
        key=lambda s: (-s["points"], s["userKey"])
    )

    top1 = standings[0]["userKey"]
    top2 = standings[1]["userKey"]

    # If there is only ONE game total and it's already between these two,
    # we treat that as the "final" for small tournaments (2 players).
    if len(games) == 1:
        r = games[0]
        if {r.get('whiteKey'), r.get('blackKey')} == {top1, top2}:
            return games  # already a head-to-head tournament

    # Check if a game between top1 and top2 already exists (any result)
    for row in games:
        wk = row.get('whiteKey')
        bk = row.get('blackKey')
        if {wk, bk} == {top1, top2}:
            # A game between them already exists (likely the final)
            return games

    # --- Create the final game between top1 and top2 ---
    g_final = game()
    g_final.start_game(top1, top2, tournamentKey=tournamentKey)

    # Reload games including the new final
    g.cur.execute(sql_games, [tournamentKey])
    games = [row for row in g.cur]
    return games



@app.route('/')
def home():
    return render_template('login.html', title='Login', msg='Welcome! Please Sign In')

@app.context_processor
def inject_user():
    return dict(me=session.get('user'))


@app.route('/login',methods = ['GET','POST'])
def login():
    un = request.form.get('name')
    pw = request.form.get('password')
    
    if un is not None and pw is not None:
        u = user()
        if u.tryLogin(un,pw):
            print(f"login ok as {u.data[0]['email']}")
            session['user'] = u.data[0]
            session['active'] = time.time()
            return redirect('main')
        else:
            print("login failed")
            return render_template('login.html', title='Login', msg='Incorrect username or password.')
    print(un)
    m = 'Welcome back'
    return render_template('login.html', title='Login', msg=m)



@app.route('/session',methods = ['GET','POST'])
def session_test():
    print(session)
    return f"{session}"

@app.route('/logout',methods = ['GET','POST'])
def logout():
    if session.get('user') is not None:
        del session['user']
        del session['active']
    return render_template('login.html', title='Login', msg='You have logged out.')

@app.route('/games')
def games_list():
    if checkSession() == False:
        return redirect('/login')

    me = session.get('user') or {}
    role = me.get('role')

    g = game()
    term = request.args.get('q', '').strip()
    rows = []

    # Admin: can see everything
    if role == 'admin':
        if term:
            like = f"%{term}%"
            sql = f"SELECT * FROM `{g.tn}` WHERE `gameID` LIKE %s ORDER BY `date` ASC;"
            g.cur.execute(sql, [like])
            rows = [row for row in g.cur]
        else:
            g.getAll(order='`date` ASC')
            rows = g.data
    else:
        # Non-admin: only see games where you're white or black
        if not me:
            return redirect('/login')

        u_obj = user()
        user_pk = u_obj.pk
        my_key = me[user_pk]

        if term:
            like = f"%{term}%"
            sql = f"""
                SELECT * FROM `{g.tn}`
                WHERE `gameID` LIKE %s
                  AND (`whiteKey` = %s OR `blackKey` = %s)
                ORDER BY `date` ASC;
            """
            g.cur.execute(sql, [like, my_key, my_key])
            rows = [row for row in g.cur]
        else:
            sql = f"""
                SELECT * FROM `{g.tn}`
                WHERE `whiteKey` = %s OR `blackKey` = %s
                ORDER BY `date` ASC;
            """
            g.cur.execute(sql, [my_key, my_key])
            rows = [row for row in g.cur]

    return render_template('games_list.html', title='Games', games=rows)



def build_board_from_moves(moves_rows):
    """
    Rebuild a python-chess Board from a list of move rows
    (each row has mv['move'] = SAN string).
    """
    board = chess.Board()
    for mv in moves_rows:
        san = mv['move']
        try:
            move_obj = board.parse_san(san)
            board.push(move_obj)
        except Exception:
            # If any bad SAN ever slipped in, skip instead of crashing
            continue
    return board


def board_to_pretty_ascii(board):
    """
    Turn the board into a nicer text representation with ranks/files labels.
    """
    rows = str(board).split('\n')  # standard 8 lines like "r n b q k b n r"
    lines = []
    for i, row in enumerate(rows):
        rank = 8 - i
        lines.append(f"{rank} {row}")
    files = "  a b c d e f g h"
    lines.append(files)
    return "\n".join(lines)


def set_game_result(gameKey, result_code):
    """
    Update the result of a game in chess_games.
    result_code must be one of: '1-0', '0-1', '0.5-0.5', '*'
    """
    g = game()
    g.getById(gameKey)
    if not g.data:
        return False

    row = g.data[0]
    row['result'] = result_code

    g.set(row)
    g.update()
    return True


@app.route('/games/new_vs/<int:opponentKey>')
def game_new_vs(opponentKey):
    """
    Start a new game: current user as White, opponent as Black.
    Then redirect both players to /games/play/<gameKey>.
    """
    if checkSession() == False:
        return redirect('/login')

    me = session.get('user')
    if not me:
        return redirect('/login')

    # get current user's primary-key field name
    u_obj = user()
    user_pk = u_obj.pk
    my_key = me[user_pk]

    # White = current user, Black = opponent
    whiteKey = my_key
    blackKey = opponentKey

    g_obj = game()
    gameKey = g_obj.start_game(whiteKey, blackKey)

    return redirect(url_for('game_play', gameKey=gameKey))




@app.route('/games/<int:gameKey>')
def game_review(gameKey):
    if checkSession() == False:
        return redirect('/login')

    g = game()
    g.getById(gameKey)
    if not g.data:
        return render_template('ok_dialog.html', msg='Game not found.')

    game_row = g.data[0]

    # Load moves in order
    m = move()
    sql = f"SELECT * FROM `{m.tn}` WHERE `gameKey` = %s ORDER BY `{m.pk}` ASC;"
    m.cur.execute(sql, [gameKey])
    moves_rows = [row for row in m.cur]

    total_moves = len(moves_rows)   
    
    try:
        ply = int(request.args.get('ply', total_moves))
    except (TypeError, ValueError):
        ply = total_moves

    if ply < 0:
        ply = 0
    if ply > total_moves:
        ply = total_moves

    # Rebuild board up to this ply
    board = chess.Board()
    for i, mv in enumerate(moves_rows[:ply]):
        san = mv['move']
        try:
            move_obj = board.parse_san(san)
            board.push(move_obj)
        except Exception:
            continue

    board_ascii = board_to_pretty_ascii(board)

    # Side to move / game over text
    result = game_row.get('result')
    if result not in (None, '', '*') and ply == total_moves:
        side_to_move = f"Game over (result: {result})"
    else:
        side_to_move = "White" if board.turn == chess.WHITE else "Black"

    # Navigation indices
    prev_ply = ply - 1 if ply > 0 else 0
    next_ply = ply + 1 if ply < total_moves else total_moves

    # Still build PGN (nice to have, but now shown compactly)
    g2 = game()
    pgn_str, fens = g2.build_pgn_and_fens(game_row, moves_rows)

    return render_template(
        'game_review.html',
        title=f"Review {game_row['gameID']}",
        game=game_row,
        gameKey=gameKey,
        moves=moves_rows,
        pgn=pgn_str,
        board_ascii=board_ascii,
        side_to_move=side_to_move,
        ply=ply,
        total_moves=total_moves,
        prev_ply=prev_ply,
        next_ply=next_ply,
    )


def get_game_state_from_db(gameKey):
    """
    Load a game + its moves from the DB and rebuild the board + FENs.

    Returns: (game_row, moves_rows, fens, board) or (None, None, None, None)
    """
    g = game()
    g.getById(gameKey)
    if not g.data:
        return None, None, None, None

    game_row = g.data[0]

    m = move()
    sql = f"SELECT * FROM `{m.tn}` WHERE `gameKey` = %s ORDER BY `{m.pk}` ASC;"
    m.cur.execute(sql, [gameKey])
    moves_rows = [row for row in m.cur]

    board = chess.Board()
    for mv in moves_rows:
        san = mv["move"]
        try:
            move_obj = board.parse_san(san)
            board.push(move_obj)
        except Exception:
            # if a bad SAN ever slips in, skip it instead of crashing
            continue

    # reuse existing helper to get PGN + FENs
    pgn_str, fens = g.build_pgn_and_fens(game_row, moves_rows)

    return game_row, moves_rows, fens, board


@app.route('/games/play/<int:gameKey>', methods=['GET', 'POST'])
def game_play(gameKey):
    """
    Web 'play' UI:
      - only white/black can move, and only on their turn
      - after any SUCCESSFUL change, redirects (PRG) so polling reloads are GETs
    """
    if checkSession() == False:
        return redirect('/login')

    # Load game row
    g = game()
    g.getById(gameKey)
    if not g.data:
        return render_template('ok_dialog.html', msg='Game not found.')

    game_row = g.data[0]

    # Load moves
    m = move()
    sql = f"SELECT * FROM `{m.tn}` WHERE `gameKey` = %s ORDER BY `{m.pk}` ASC;"
    m.cur.execute(sql, [gameKey])
    moves_rows = [row for row in m.cur]

    error = None
    info = None  # kept in case you want to show messages later

    if request.method == 'POST':
        command = request.form.get('command')
        san = (request.form.get('san') or '').strip()

        # Rebuild board from existing moves
        board = build_board_from_moves(moves_rows)

        current_result = game_row.get('result')
        game_over = current_result not in (None, '', '*')
        status = game_row.get('status') or 'active'   # for future use

        # Who is logged in?
        me = session.get('user')
        current_user_key = None
        if me:
            u_obj = user()
            current_user_key = me.get(u_obj.pk)

        whiteKey = game_row.get('whiteKey')
        blackKey = game_row.get('blackKey')

        # ---- Permission / state checks ----
        if game_over:
            error = (
                f"Game is already over (result: {current_result}). "
                "No more moves allowed."
            )
        elif current_user_key is None:
            error = "Could not determine current user; please log in again."
        elif current_user_key not in (whiteKey, blackKey):
            error = "Only the two players in this game can make moves."
        elif status == 'pending':
            error = "This game has not been accepted yet."
        else:
            is_white_turn = (board.turn == chess.WHITE)
            if is_white_turn and current_user_key != whiteKey:
                error = "It is White's turn; only White may move or resign."
            elif (not is_white_turn) and current_user_key != blackKey:
                error = "It is Black's turn; only Black may move or resign."
            else:
                # ---- PERMISSION OK: apply commands ----

                # RESIGN
                if command == 'resign':
                    made_by = 'W' if board.turn == chess.WHITE else 'B'
                    result_code = '0-1' if made_by == 'W' else '1-0'
                    set_game_result(gameKey, result_code)
                    # info = f"Player {made_by} resigned. Result set to {result_code}."
                    return redirect(url_for('game_play', gameKey=gameKey))

                # DIRECT RESULT
                elif san.lower() in ['1-0', '0-1', '0.5-0.5']:
                    result_code = san.lower()
                    set_game_result(gameKey, result_code)
                    # info = f"Game result set to {result_code}."
                    return redirect(url_for('game_play', gameKey=gameKey))

                # NORMAL MOVE
                elif san:
                    try:
                        move_obj = board.parse_san(san)
                        board.push(move_obj)

                        made_by = 'W' if len(moves_rows) % 2 == 0 else 'B'

                        m_new = move()
                        m_new.add_move(gameKey, san, made_by)

                        # SUCCESS: redirect so the page becomes a GET
                        return redirect(url_for('game_play', gameKey=gameKey))

                    except Exception as e:
                        # Illegal move: stay on this page (no redirect),
                        # so the user sees the error and can correct it.
                        error = f"Illegal move: {e}"
                else:
                    error = "Please enter a move in SAN notation or use the resign button."

        # If we got here WITHOUT redirect, either it was an error or no change.
        # Reload latest game row for accurate display.
        g.getById(gameKey)
        if g.data:
            game_row = g.data[0]

        # Also reload moves if needed (for error display / consistency)
        m.cur.execute(sql, [gameKey])
        moves_rows = [row for row in m.cur]

    # --- GET or POST-with-error: render page ---
    board = build_board_from_moves(moves_rows)
    board_ascii = board_to_pretty_ascii(board)

    result = game_row.get('result')
    if result not in (None, '', '*'):
        side_to_move = f"Game over (result: {result})"
    else:
        side_to_move = "White" if board.turn == chess.WHITE else "Black"

    return render_template(
        'game_play.html',
        title=f"Play {game_row['gameID']}",
        game=game_row,
        moves=moves_rows,
        error=error,
        info=info,
        board_ascii=board_ascii,
        side_to_move=side_to_move,
    )


@app.route('/tournaments/start', methods=['POST'])
def tournament_start():

    if checkSession() == False:
        return redirect('/login')

    me = session.get('user') or {}
    if me.get('role') != 'admin':
        return render_template('ok_dialog.html', msg="Only admin can start a tournament.")

    pkval = request.form.get('pkval')
    if not pkval:
        return render_template('ok_dialog.html', msg="Tournament not specified.")

    # Load tournament
    t = tournament()
    t.getById(pkval)
    if not t.data:
        return render_template('ok_dialog.html', msg="Tournament not found.")
    trow = t.data[0]

    # Check if it already has games
    g = game()
    sql_games = f"SELECT COUNT(*) AS cnt FROM `{g.tn}` WHERE `tournamentKey` = %s;"
    g.cur.execute(sql_games, [pkval])
    row = g.cur.fetchone()
    if row and row.get('cnt', 0) > 0:
        return render_template('ok_dialog.html', 
                               msg="This tournament already has games. (You can add more later if needed.)")

    # Get participants
    te = tournamentEntry()
    entries = te.get_for_tournament(pkval)
    player_keys = [e['userKey'] for e in entries]

    if len(player_keys) < 2:
        return render_template('ok_dialog.html', msg="Need at least 2 players to start a tournament.")

    n = len(player_keys)
    # require n = 2,4,8,16,... (single-elim bracket)
    if n & (n - 1) != 0:
        return render_template(
            'ok_dialog.html',
            msg=f"{n} players registered. For now, bracket requires a power of 2 (2, 4, 8, 16, ...)."
        )


    random.shuffle(player_keys)

    g_obj = game()
    created_games = []
    for i in range(0, len(player_keys), 2):
        whiteKey = player_keys[i]
        blackKey = player_keys[i + 1]
        gameKey = g_obj.start_game(whiteKey, blackKey, tournamentKey=pkval, round=1)
        created_games.append(gameKey)

    msg = (
        f"Started tournament '{trow.get('name')}' with {len(player_keys)} players. "
        f"Created {len(created_games)} games."
    )
    return render_template('ok_dialog.html', msg=msg)



@app.route('/tournaments/standings')
def tournament_standings():
    if checkSession() == False:
        return redirect('/login')

    pkval = request.args.get('pkval')
    if not pkval:
        return render_template('ok_dialog.html', msg="Tournament not specified.")

    # Load tournament
    t = tournament()
    t.getById(pkval)
    if not t.data:
        return render_template('ok_dialog.html', msg="Tournament not found.")
    trow = t.data[0]

    # Participants + user info
    te = tournamentEntry()
    u = user()

    sql_participants = f"""
        SELECT u.`{u.pk}` AS userKey,
               u.`userID`,
               u.`Fname`,
               u.`Lname`
        FROM `{te.tn}` te
        JOIN `{u.tn}` u
          ON te.`userKey` = u.`{u.pk}`
        WHERE te.`tournamentKey` = %s;
    """
    te.cur.execute(sql_participants, [pkval])
    participants = [row for row in te.cur]

    # Initialise stats
    stats = {}
    for p in participants:
        uk = p['userKey']
        stats[uk] = {
            "userKey": uk,
            "userID": p['userID'],
            "name": f"{p.get('Fname','')} {p.get('Lname','')}".strip(),
            "points": 0.0,
            "wins": 0,
            "draws": 0,
            "losses": 0,
        }

    # Read games in this tournament
    g = game()
    sql_games = f"SELECT * FROM `{g.tn}` WHERE `tournamentKey` = %s;"
    g.cur.execute(sql_games, [pkval])
    games = [row for row in g.cur]

    # Update scores
    for row in games:
        result = row.get('result')
        whiteKey = row.get('whiteKey')
        blackKey = row.get('blackKey')

        if result == '1-0':
            if whiteKey in stats:
                stats[whiteKey]["points"] += 1.0
                stats[whiteKey]["wins"] += 1
            if blackKey in stats:
                stats[blackKey]["losses"] += 1

        elif result == '0-1':
            if blackKey in stats:
                stats[blackKey]["points"] += 1.0
                stats[blackKey]["wins"] += 1
            if whiteKey in stats:
                stats[whiteKey]["losses"] += 1

        elif result == '0.5-0.5':
            if whiteKey in stats:
                stats[whiteKey]["points"] += 0.5
                stats[whiteKey]["draws"] += 1
            if blackKey in stats:
                stats[blackKey]["points"] += 0.5
                stats[blackKey]["draws"] += 1

        # ignore result '*' or None: game not finished yet

    # Sort by points descending, then by userID
    standings = sorted(
        stats.values(),
        key=lambda s: (-s["points"], s["userID"])
    )

    return render_template(
        'tournaments/standings.html',
        title=f"Standings: {trow.get('name')}",
        tournament=trow,
        standings=standings,
        games=games,
    )



@app.route('/games/new')
def games_new_choose():
    """
    Let the logged-in user choose an opponent (or play vs self)
    before we actually create the game.
    """
    if checkSession() == False:
        return redirect('/login')

    me = session.get('user')
    if not me:
        return redirect('/login')

    u = user()

    # Load all player-type users (you can adjust this filter if you want)
    sql = f"SELECT * FROM `{u.tn}` WHERE `role` = %s ORDER BY `userID` ASC;"
    u.cur.execute(sql, ['player'])
    users = [row for row in u.cur]

    return render_template(
        'games_new.html',
        title='Start a new game',
        users=users,
        me=me,
    )



@app.route('/games/play/new')
def game_play_new():

    if checkSession() == False:
        return redirect('/login')

    me = session.get('user')
    if not me:
        return redirect('/login')
    
    whiteKey = me['userKey']
    blackKey = me['userKey']
    g = game()
    gameKey = g.start_game(whiteKey, blackKey)

    return redirect(url_for('game_play', gameKey=gameKey))




@app.route('/api/game/<int:gameKey>')
def api_game_state(gameKey):
    """Return current game state (moves + FEN) as JSON."""
    if checkSession() == False:
        return jsonify({"success": False, "error": "not authenticated"}), 401

    game_row, moves_rows, fens, board = get_game_state_from_db(gameKey)
    if game_row is None:
        return jsonify({"success": False, "error": "game not found"}), 404

    return jsonify({
        "success": True,
        "game": {
            "gameKey": gameKey,
            "gameID": game_row["gameID"],
            "result": game_row.get("result"),
        },
        "moves": [
            {
                "san": mv["move"],
                "madeBy": mv["madeBy"],
                "moveKey": mv["moveKey"],
            }
            for mv in moves_rows
        ],
        "fens": fens,
        "currentFen": fens[-1] if fens else chess.Board().fen(),
    })


@app.route('/api/game/<int:gameKey>/move', methods=['POST'])
def api_game_add_move(gameKey):
    if checkSession() == False:
        return jsonify({"success": False, "error": "not authenticated"}), 401

    data = request.get_json(silent=True) or {}
    san = (data.get("san") or "").strip()

    if not san:
        return jsonify({"success": False, "error": "No move provided."}), 400

    game_row, moves_rows, fens, board = get_game_state_from_db(gameKey)
    if game_row is None:
        return jsonify({"success": False, "error": "Game not found."}), 404

    # Optional: prevent moves if result is already set
    if game_row.get("result") and game_row["result"] != "*":
        return jsonify({"success": False, "error": "Game already finished."}), 400

    # --- NEW: who is making the move? ---
    me = session.get('user')
    u_obj = user()
    user_pk = u_obj.pk
    current_user_key = me[user_pk]

    whiteKey = game_row.get("whiteKey")
    blackKey = game_row.get("blackKey")

    is_white_turn = (board.turn == chess.WHITE)

    if is_white_turn and current_user_key != whiteKey:
        return jsonify({"success": False, "error": "It is White's turn."}), 403
    if not is_white_turn and current_user_key != blackKey:
        return jsonify({"success": False, "error": "It is Black's turn."}), 403

    # Whose turn is it?
    made_by = "W" if board.turn == chess.WHITE else "B"


    # validate SAN against current board
    try:
        move_obj = board.parse_san(san)
    except Exception as e:
        return jsonify({"success": False, "error": f"Illegal move: {e}"}), 400

    board.push(move_obj)

    # store in DB
    m_obj = move()
    m_obj.add_move(gameKey, san, made_by)

    # rebuild state to send back
    game_row, moves_rows, fens, board = get_game_state_from_db(gameKey)

    return jsonify({
        "success": True,
        "moves": [
            {
                "san": mv["move"],
                "madeBy": mv["madeBy"],
                "moveKey": mv["moveKey"],
            }
            for mv in moves_rows
        ],
        "fens": fens,
        "currentFen": fens[-1] if fens else chess.Board().fen(),
    })




@app.route('/users/manage', methods=['GET', 'POST'])
def manage_user():
    if checkSession() == False:
        return redirect('/login')

    o = user()
    action = request.args.get('action')
    pkval = request.args.get('pkval')

    # --------------------
    # DELETE
    # --------------------
    if action == 'delete' and pkval is not None:
        o.deleteById(pkval)
        return render_template('ok_dialog.html', msg=f"User ID {pkval} deleted.")

    # --------------------
    # INSERT (new user)
    # --------------------
    if action == 'insert':
        d = {}

        # Core identification fields
        d['userID'] = (request.form.get('userID') or '').strip()
        d['Fname'] = (request.form.get('Fname') or '').strip()
        d['Lname'] = (request.form.get('Lname') or '').strip()

        # Contact / meta
        d['email'] = (request.form.get('email') or '').strip()
        d['country'] = (request.form.get('country') or '').strip().upper()
        d['DOB'] = request.form.get('DOB') or None

        rating_str = (request.form.get('rating') or '').strip()
        d['rating'] = int(rating_str) if rating_str.isdigit() else None

        d['title'] = (request.form.get('title') or '').strip()
        d['role'] = request.form.get('role')

        # Passwords
        d['password'] = request.form.get('password') or ''
        d['password2'] = request.form.get('password2') or ''

        o.set(d)

        if o.verify_new():
            o.insert()
            return render_template(
                'ok_dialog.html',
                msg=f"User {o.data[0]['userID']} added."
            )
        else:
            # show form again with errors
            return render_template('users/add.html', obj=o)

    # --------------------
    # UPDATE (existing user)
    # --------------------
    if action == 'update' and pkval is not None:
        o.getById(pkval)
        if not o.data:
            return render_template('ok_dialog.html', msg="User not found.")

        row = o.data[0]

        # Update base fields from form
        row['userID'] = (request.form.get('userID') or row.get('userID', '')).strip()
        row['Fname'] = (request.form.get('Fname') or row.get('Fname', '')).strip()
        row['Lname'] = (request.form.get('Lname') or row.get('Lname', '')).strip()
        row['email'] = (request.form.get('email') or row.get('email', '')).strip()
        row['country'] = (request.form.get('country') or row.get('country', '')).strip().upper()
        row['DOB'] = request.form.get('DOB') or row.get('DOB')

        rating_str = (request.form.get('rating') or '').strip()
        if rating_str:
            try:
                row['rating'] = int(rating_str)
            except ValueError:
                row['rating'] = row.get('rating')
        # if left blank, keep old rating

        row['title'] = (request.form.get('title') or row.get('title', '')).strip()
        row['role'] = request.form.get('role') or row.get('role')

        # Only touch password if user actually typed something
        pw = request.form.get('password') or ''
        pw2 = request.form.get('password2') or ''
        if pw or pw2:
            row['password'] = pw
            row['password2'] = pw2

        if o.verify_update():
            o.update()
            return render_template('ok_dialog.html', msg="User updated.")
        else:
            return render_template('users/manage.html', obj=o)

    if pkval is None:
        term = request.args.get('q', '').strip()
        if term:
            like = f"%{term}%"
            sql = f"SELECT * FROM `{o.tn}` WHERE `userID` LIKE %s OR `email` LIKE %s ORDER BY `userID` ASC;"
            o.cur.execute(sql, [like, like])
            o.data = [row for row in o.cur]
        else:
            o.getAll(order='`userID` ASC')

        return render_template('users/list.html', obj=o)

    if pkval == 'new':
        o.errors = []
        o.data = [{
            'userID': '',
            'Fname': '',
            'Lname': '',
            'email': '',
            'country': '',
            'DOB': '',
            'rating': '',
            'title': '',
            'role': 'player',
            'password': '',
            'password2': '',
        }]
        return render_template('users/add.html', obj=o)

    # EDIT EXISTING
    o.getById(pkval)
    if not o.data:
        return render_template('ok_dialog.html', msg="User not found.")
    return render_template('users/manage.html', obj=o)

@app.route('/users/search')
def search_users_web():
    if checkSession() == False:
        return redirect('/login')

    u = user()
    term = request.args.get('q', '').strip()

    if term:
        like = f"%{term}%"
        sql = f"SELECT * FROM `{u.tn}` WHERE `userID` LIKE %s OR `email` LIKE %s ORDER BY `userID` ASC;"
        u.cur.execute(sql, [like, like])
        rows = [row for row in u.cur]
    else:
        u.getAll(order='`userID` ASC')
        rows = u.data

    return render_template('users/search.html', title='Search users', users=rows)



@app.route('/tournaments/participants')
def tournament_participants():
    if checkSession() == False:
        return redirect('/login')

    pkval = request.args.get('pkval')
    if pkval is None:
        return render_template('ok_dialog.html', msg="Tournament not specified.")

    # Load tournament
    t = tournament()
    t.getById(pkval)
    if not t.data:
        return render_template('ok_dialog.html', msg="Tournament not found.")

    trow = t.data[0]

    # Load participants
    te = tournamentEntry()
    entries = te.get_for_tournament(pkval)

    # Fetch user info for each participant
    u = user()
    participants = []
    for entry in entries:
        u.getById(entry['userKey'])
        if u.data:
            participants.append(u.data[0])

    return render_template(
        'tournaments/participants.html',
        tournament=trow,
        participants=participants
    )

@app.route('/tournaments')
def tournaments_user():
    if checkSession() == False:
        return redirect('/login')

    me = session.get('user')
    if not me:
        return redirect('/login')

    # get current user's PK value
    u_obj = user()
    user_pk = u_obj.pk
    user_id = me[user_pk]

    t = tournament()
    te = tournamentEntry()

    term = request.args.get('q', '').strip()
    if term:
        like = f"%{term}%"
        sql = f"""SELECT * FROM `{t.tn}`
                  WHERE `tournamentID` LIKE %s OR `name` LIKE %s
                  ORDER BY `tournamentID` ASC;"""
        t.cur.execute(sql, [like, like])
        rows = [row for row in t.cur]
    else:
        t.getAll(order='`tournamentID` ASC')
        rows = t.data

    pk_field = t.pk
    tournaments = []
    for r in rows:
        pkval = r[pk_field]
        entries = te.get_for_tournament(pkval)
        current_count = len(entries)
        is_reg = any(e['userKey'] == user_id for e in entries)

        info = dict(r)
        info['_pk'] = pkval
        info['_current_count'] = current_count
        info['_is_registered'] = is_reg
        tournaments.append(info)

    return render_template(
        'tournaments/user_list.html',
        title='Tournaments',
        tournaments=tournaments
    )



@app.route('/users/profile/<int:userKey>')
def user_profile(userKey):
    if checkSession() == False:
        return redirect('/login')

    # --- Load basic user info ---
    u = user()
    u.getById(userKey)
    if not u.data:
        return render_template('ok_dialog.html', msg="User not found.")
    profile = u.data[0]

    # --- Load all games this user has played ---
    g = game()
    sql_games = f"""
        SELECT * FROM `{g.tn}`
        WHERE `whiteKey` = %s OR `blackKey` = %s
        ORDER BY `date` DESC;
    """
    g.cur.execute(sql_games, [userKey, userKey])
    games = [row for row in g.cur]

    # --- Compute simple stats ---
    total = len(games)
    wins = losses = draws = ongoing = 0
    for row in games:
        result = row.get('result')
        white_key = row.get('whiteKey')
        black_key = row.get('blackKey')

        if result == '1-0':
            if userKey == white_key:
                wins += 1
            elif userKey == black_key:
                losses += 1
        elif result == '0-1':
            if userKey == black_key:
                wins += 1
            elif userKey == white_key:
                losses += 1
        elif result == '0.5-0.5':
            draws += 1
        else:
            ongoing += 1

    stats = {
        "total": total,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "ongoing": ongoing,
    }

    # --- Tournaments this user is registered in ---
    t = tournament()
    te = tournamentEntry()

    sql_tournaments = f"""
        SELECT t.*
        FROM `{t.tn}` t
        JOIN `{te.tn}` te
          ON t.`{t.pk}` = te.`tournamentKey`
        WHERE te.`userKey` = %s
        ORDER BY t.`tournamentID` ASC;
    """
    te.cur.execute(sql_tournaments, [userKey])
    tournaments = [row for row in te.cur]

    return render_template(
        'users/profile.html',
        title=f"Profile: {profile.get('userID')}",
        profile=profile,
        stats=stats,
        games=games,
        tournaments=tournaments,
    )


@app.route('/tournaments/signup')
def tournament_signup_web():
    if checkSession() == False:
        return redirect('/login')

    me = session.get('user')
    if not me:
        return redirect('/login')

    pkval = request.args.get('pkval')
    if pkval is None:
        return render_template('ok_dialog.html', msg="Tournament not specified.")

    t = tournament()
    t.getById(pkval)
    if not t.data:
        return render_template('ok_dialog.html', msg="Tournament not found.")

    trow = t.data[0]
    person_limit = trow.get('personLimit')

    te = tournamentEntry()
    current_count = len(te.get_for_tournament(pkval))

    u_obj = user()
    user_pk = u_obj.pk
    user_id = me[user_pk]

    if te.is_registered(user_id, pkval):
        return render_template('ok_dialog.html', msg="You are already registered for this tournament.")

    if person_limit is not None and current_count >= person_limit:
        return render_template(
            'ok_dialog.html',
            msg=f"Sorry, this tournament is full ({current_count}/{person_limit} players)."
        )

    te.register(user_id, pkval)
    return redirect(url_for('tournaments_user'))


@app.route('/tournaments/withdraw')
def tournament_withdraw_web():
    if checkSession() == False:
        return redirect('/login')

    me = session.get('user')
    if not me:
        return redirect('/login')

    pkval = request.args.get('pkval')
    if pkval is None:
        return render_template('ok_dialog.html', msg="Tournament not specified.")

    te = tournamentEntry()
    u_obj = user()
    user_pk = u_obj.pk
    user_id = me[user_pk]

    if te.is_registered(user_id, pkval):
        te.unregister(user_id, pkval)
        return redirect(url_for('tournaments_user'))
    else:
        return render_template('ok_dialog.html', msg="You are not registered for this tournament.")

@app.route('/games/play')
def play_game_web():
    if checkSession() == False:
        return redirect('/login')

    return render_template(
        'ok_dialog.html',
        msg="Play-a-game via web is not implemented yet. Use the CLI version for now."
    )


@app.route('/main')
def main():
    if checkSession() == False:
        return redirect('/login')
    me = session.get('user')
    return render_template('main.html', title='Main menu', me=me)

# endpoint route for static files
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


#standalone function to be called when we need to check if a user is logged in.
def checkSession():
    if 'active' in session.keys():
        timeSinceAct = time.time() - session['active']
        #print(timeSinceAct)
        if timeSinceAct > 500:
            session['msg'] = 'Your session has timed out.'
            return False
        else:
            session['active'] = time.time()
            return True
    else:
        return False  




@app.route('/tournaments/manage', methods=['GET', 'POST'])
def manage_tournament():
    if checkSession() == False:
        return redirect('/login')

    me = session.get('user') or {}
    if me.get('role') != 'admin':
        return render_template('ok_dialog.html', msg='Admin only.')

    o = tournament()
    action = request.args.get('action')
    pkval = request.args.get('pkval')

    if action == 'delete' and pkval is not None:
        o.deleteById(pkval)
        return render_template('ok_dialog.html', msg=f"Tournament ID {pkval} deleted.")

    if action == 'insert':
        d = {}
        d['tournamentID'] = (request.form.get('tournamentID') or '').strip()
        d['name']         = (request.form.get('name') or '').strip()
        d['location']     = (request.form.get('location') or '').strip()

        rating_str = (request.form.get('ratingLimit') or '').strip()
        d['ratingLimit'] = int(rating_str) if rating_str.isdigit() else None

        people_str = (request.form.get('personLimit') or '').strip()
        d['personLimit'] = int(people_str) if people_str.isdigit() else None

        o.set(d)
        if hasattr(o, 'verify_new'):
            ok = o.verify_new()
        else:
            ok = True

        if ok:
            o.insert()
            return render_template('ok_dialog.html',
                                   msg=f"Tournament {o.data[0]['tournamentID']} added.")
        else:
            return render_template('tournaments/add.html', obj=o)

    if action == 'update' and pkval is not None:
        o.getById(pkval)
        if not o.data:
            return render_template('ok_dialog.html', msg="Tournament not found.")

        row = o.data[0]
        row['tournamentID'] = (request.form.get('tournamentID') or row.get('tournamentID','')).strip()
        row['name']         = (request.form.get('name') or row.get('name','')).strip()
        row['location']     = (request.form.get('location') or row.get('location','')).strip()

        rating_str = (request.form.get('ratingLimit') or '').strip()
        if rating_str:
            try:
                row['ratingLimit'] = int(rating_str)
            except ValueError:
                pass

        people_str = (request.form.get('personLimit') or '').strip()
        if people_str:
            try:
                row['personLimit'] = int(people_str)
            except ValueError:
                pass


        if hasattr(o, 'verify_update'):
            ok = o.verify_update()
        else:
            ok = True

        if ok:
            o.update()
            return render_template('ok_dialog.html', msg="Tournament updated.")
        else:
            return render_template('tournaments/manage.html', obj=o)

    if pkval is None:
        term = request.args.get('q', '').strip()
        if term:
            like = f"%{term}%"
            sql = f"""SELECT * FROM `{o.tn}`
                      WHERE `tournamentID` LIKE %s OR `name` LIKE %s
                      ORDER BY `tournamentID` ASC;"""
            o.cur.execute(sql, [like, like])
            o.data = [row for row in o.cur]
        else:
            o.getAll(order='`tournamentID` ASC')
        return render_template('tournaments/list.html', obj=o)

    if pkval == 'new':
        o.errors = []
        o.data = [{
            'tournamentID': '',
            'name': '',
            'location': '',
            'ratingLimit': '',
            'personLimit': '',
        }]
        return render_template('tournaments/add.html', obj=o)

    o.getById(pkval)
    if not o.data:
        return render_template('ok_dialog.html', msg="Tournament not found.")
    return render_template('tournaments/manage.html', obj=o)


@app.route('/tournaments/games')
def tournament_games():
    """
    List all games belonging to a specific tournament.
    Also: if all games in the highest round are finished and the next round
    doesn't exist yet, automatically create the next knockout round.
    """
    if checkSession() == False:
        return redirect('/login')

    pkval = request.args.get('pkval')
    if not pkval:
        return render_template('ok_dialog.html', msg="Tournament not specified.")

    # Load tournament
    t = tournament()
    t.getById(pkval)
    if not t.data:
        return render_template('ok_dialog.html', msg="Tournament not found.")
    trow = t.data[0]

    # Advance bracket if possible
    all_games = maybe_advance_knockout_round(pkval)

    # Reload games with player names for display
    g = game()
    u = user()
    sql = f"""
        SELECT g.*,
               w.`userID` AS whiteID,
               b.`userID` AS blackID
        FROM `{g.tn}` g
        LEFT JOIN `{u.tn}` w ON g.`whiteKey` = w.`{u.pk}`
        LEFT JOIN `{u.tn}` b ON g.`blackKey` = b.`{u.pk}`
        WHERE g.`tournamentKey` = %s
        ORDER BY g.`round` ASC, g.`date` ASC, g.`gameID` ASC;
    """
    g.cur.execute(sql, [pkval])
    games_with_names = [row for row in g.cur]

    return render_template(
        'tournaments/games.html',
        title=f"Games – {trow.get('name')}",
        tournament=trow,
        games=games_with_names,
    )




if __name__ == '__main__':
   app.run(host='0.0.0.0',debug=True)   