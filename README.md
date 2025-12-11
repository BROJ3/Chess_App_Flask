# ToniChess

A Flask web application for running a lightweight chess club: manage users, create tournaments, play games, and review results directly in the browser. The app stores data in MySQL and uses the [python-chess](https://python-chess.readthedocs.io/) library to validate moves and render games in SAN/ASCII form.

## Features
- **User management** – Admins can create, edit, and delete users; players can log in with either their `userID` or email. Passwords are salted and hashed before storage.
- **Tournament control** – Create tournaments with rating and participant limits, enroll players, launch events, and automatically spawn knockout rounds or finals based on completed results.
- **Game play and review** – Start games between participants, enter SAN moves, navigate through the move list, and review finished games with board states recreated via python-chess.
- **Sample data for demos** – An initialization script can create tables plus demo users, tournaments, and games so the UI is immediately populated.

## Project layout
- `app_flask.py` – Flask app with routes for authentication, tournaments, games, and review flows.
- `baseObject.py` – Base CRUD helper that reads table names and credentials from `config.yml`.
- `user.py`, `tournament.py`, `tournament_entry.py`, `game.py`, `move.py` – Data-layer classes for each entity.
- `templates/` – Jinja templates for login, dashboards, tournaments, and game play/review screens.
- `static/` – Shared CSS and assets.
- `initializing.py` – Optional bootstrap script for creating MySQL tables and loading sample data.

## Requirements
- Python 3.10+
- MySQL 5.7+ or MariaDB
- Pip packages: `flask`, `flask-session`, `pymysql`, `pyyaml`, `python-chess`

Install the dependencies:

```bash
pip install flask flask-session pymysql pyyaml python-chess
```

## Configuration
Copy the example configuration to `config.yml` and fill in your MySQL credentials and table names:

```yaml
# config.yml

db:
  user: "your_username"
  pw: "your_password"
  host: "localhost"
  db: "tonichess"

tables:
  user: "chess_users"
  tournament: "chess_tournaments"
  game: "chess_games"
  move: "chess_moves"
  tournamentEntry: "tournamentEntry"
```

> Keep `config.yml` out of version control because it contains secrets.

## Database setup (optional)
Run the bootstrap script after configuring the database to create the tables and load demo rows:

```bash
python initializing.py
```

The seed data includes an admin account (`toni01` / `123`) and several player accounts (e.g., `tal01` / `123`, `carlsen` / `123`).

## Running the app
Start the Flask development server:

```bash
python app_flask.py
```

Visit `http://127.0.0.1:5000` and log in with one of the seeded accounts, or create your own via the admin interface.

## Development notes
- Session data is stored on the filesystem via `Flask-Session`.
- Game logic uses python-chess for move validation and board representation.
- Tournament helpers can automatically add tiebreak games and advance knockout rounds when results are available.

## Contributing
Issues and pull requests are welcome. If you add new database tables or configuration values, document them in `config_example.yml` so others can set up their environments easily.