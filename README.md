🟩 ToniChess – Flask Chess Management & Gameplay System

ToniChess is a full-stack web application built with Flask that allows users to play chess, review chess games, manage tournaments, manage users, and track statistics, all through a clean interface inspired by chess.com.

It includes authentication, admin/user roles, tournament creation, pairing, game gameplay in SAN notation, ASCII board visualization, and a polished two-column layout for all major pages.

📸 Screenshots

(Add your screenshots into a screenshots/ folder)

Main Menu

Manage Users

Manage Tournaments

Play Game (Board + Moves)

Review Game

🧩 Features
🔐 Authentication & Roles

Login/logout system

Custom login navbar: “Welcome Toni — ToniChess”

Admin & standard user permissions

👤 User Management (Admin)

Admins can:

Create users

Edit user data

Delete users

Search and filter users

View user profiles

View user game history & statistics

User fields include rating, title (GM/IM/etc), country, email, and account role.

🏆 Tournament Management

Admins can:

Create/Edit/Delete tournaments

Control rating limits & player caps

View participants

Generate pairings by starting the tournament

View tournament standings (Wins / Draws / Losses / Points)

Players can:

Sign up for tournaments

Withdraw

View tournament games

♟ Game System

Each game supports:

SAN move entry (e4, Nf3, O-O, etc.)

Move validation

Board updates after each move

ASCII-rendered chessboard

Navigation for reviewing games:

First, Prev, Next, Last

Real-time board refresh logic (polling)

End-of-game recognition (1-0, 0-1, ½-½)

🖥 UI Layout System

Across the entire app, pages use a two-column responsive layout:

Left column for main content

Right column for secondary content (moves, tables, stats)

Clean spacing and modern card-style content blocks

Mobile-responsive stacking layout

Centered content area with gentle padding

Specific examples:

Play Game: board on left, moves on right

Review Game: board + navigation on left, move list on right

Profile: user info on left, tables on right

Login: banner + login form

⚙️ Installation
1. Clone the repository
git clone https://github.com/BROJ3/Chess_App_Flask.git
cd Chess_App_Flask

2. Install Python dependencies
pip install -r requirements.txt


If the file is missing, install manually:

Flask
PyMySQL
PyYAML

🗄 Database Setup (MySQL)
1. Create the database
CREATE DATABASE tonichess;

2. Configure credentials

Your config.yml file should look like:

db:
  user: "your_username"
  pw: "your_password"
  host: "localhost"
  db: "tonichess"

tables:
  user: "users"
  tournament: "tournaments"
  game: "games"
  move: "moves"
  tournamentEntry: "entries"

3. Ensure config.yml is ignored:

Add this to .gitignore:

config.yml
__pycache__/
*.pyc

🚀 Running the Application

Start the server:

python app_flask.py


Then open in your browser:

http://127.0.0.1:5000


or your server IP if hosted remotely.

🧠 How the App Works (Workflow)
1. Login

You log in through a custom-styled login page with a welcome banner.

2. Main Menu

Players see:

Search users

Browse tournaments

Sign up / withdraw

Start new games

Review games

Admins see additional management tools.

3. Starting a Game

SAN move input updates the ASCII board automatically.

4. Reviewing a Game

The two-column layout shows:

Board & move navigation (left)

Full move list (right)

5. Managing Users

Admins can modify accounts, inspect stats, and see all games connected to that user.

6. Managing Tournaments

Admins can create tournaments, edit them, delete them, manage players, and start tournaments to generate pairings.

📁 Folder Structure
Chess_App_Flask/
│
├── app_flask.py            # Main server application
├── objects/                # Classes for User, Game, Tournament, Move
├── templates/              # All HTML/Jinja templates
│   ├── base.html
│   ├── loginbase.html
│   ├── users/
│   ├── tournaments/
│   ├── games/
│   └── ...
│
├── static/
│   └── style.css           # Application-wide CSS
│
├── config.yml              # Local DB credentials (ignored in git)
└── README.md               # This file

🛠 Developer Notes
UI Layout

All major pages use:

<div class="layout-two-col">
    <div class="col-left"> ... </div>
    <div class="col-right"> ... </div>
</div>


Empty right columns are automatically hidden.

Board Rendering

The ASCII board uses:

Monospace font

Locked line-height

white-space: pre for alignment

Login Banner

loginbase.html includes:

Welcome Toni — ToniChess


to brand the login experience.

📌 Future Improvements (Optional)

Replace ASCII with graphical chessboard

Swiss-system or round-robin tournament generator

PGN import/export

User avatars + profiles

Elo rating adjustments

Websockets for live updating

🤝 Contributing

Pull requests are welcome.
Open issues for bugs, improvement ideas, or UI enhancements.