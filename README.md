🟩 ToniChess – A Web Application for Managing and Playing Chess

ToniChess is a Flask-based web application designed to bring chess club management, tournament organization, and game play into a single, easy-to-use platform. Built with both players and administrators in mind, the system provides tools for creating users, running tournaments, tracking statistics, and playing or reviewing chess games directly inside the browser. The interface is intentionally simple, clean, and inspired by the usability of major chess websites.

At its core, ToniChess offers a structured but lightweight environment where users can log in, participate in tournaments, start games, submit moves using SAN notation, and review entire game histories. Administrators benefit from expanded capabilities, including full user management, tournament creation, editing, deletion, and oversight of player activity across the platform.

📸 Screenshots

(Add your own screenshots following this structure)

Main Menu


Manage Users


Manage Tournaments


Play Game


Review Game


🧭 Overview of the Application
A Unified Chess Management Platform

The application combines several components often handled by separate tools: authentication, user management, tournament tracking, game storage, and a complete system for playing or reviewing chess games. Users interact with the system through a clean two-column layout that centers content on the page and organizes information intuitively. Players access the features they need most—such as viewing tournaments, starting a new game, or browsing completed games—while administrators gain access to an expanded management menu.

Game Logic and Presentation

Games are played using SAN (Standard Algebraic Notation). Each move updates an internally stored game state and is rendered as a classic ASCII chessboard. Despite the textual nature of the board, the interface is polished and easy to follow. The board appears in the left column, while the complete move list—along with navigation tools for stepping through the game—appears in the right column.

The game review system allows users to step forward and backward through a game using buttons such as First, Prev, Next, and Last, recreating the experience of replaying a PGN while staying entirely inside the web interface.

Tournament and User Ecosystems

Administrators can create tournaments, adjust rating and participant limits, and manage entries. Once a tournament is started, pairings are created automatically, and games begin appearing in the system. Each user has a profile page that includes basic account information, country, rating, title, and full career statistics—wins, losses, draws, and ongoing matches.

🖥️ User Interface and Layout Philosophy

The application uses a consistent, responsive two-column design intended to mimic the clarity and structure of chess.com-style layouts while remaining lightweight.

The left column always presents the primary content: login form, user information, tournament details, chessboard, or control panel.

The right column displays contextual or supporting information: tables, move lists, or tournament standings.

Content is grouped inside card-style containers with subtle shadows and padding for readability.

Pages automatically reflow on smaller screens, stacking vertically when needed.

On pages where only one column is required (e.g., the login screen), the right column collapses automatically, allowing the left column to comfortably expand.

This design is consistent across all pages, contributing to a smooth and predictable user experience.

⚙️ Installation and Setup

To run the application locally, begin by cloning the repository:

git clone https://github.com/BROJ3/Chess_App_Flask.git
cd Chess_App_Flask


Install the required Python packages:

pip install -r requirements.txt


If no requirements file is available, you will need the core dependencies:

Flask

PyMySQL

PyYAML

The application relies on a MySQL database. After creating one (for example, named tonichess), configure your credentials in a config.yml file:

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


Be sure your config.yml is excluded from Git version control, as it contains sensitive credentials:

config.yml
__pycache__/
*.pyc


Once configured, you can launch the server by running:

python app_flask.py


The application will be available at:

http://127.0.0.1:5000

♟️ Using ToniChess
Logging In

Upon launching the application, users are greeted with a custom welcome banner on the login page. After authenticating, the system directs the user to the main menu, where available features depend on their assigned role.

Player Experience

Players can:

Browse tournaments

Sign up or withdraw

Start new games

Enter moves in an active game

Review completed games

View their personal statistics and game history

In the game view, players enter moves as SAN notation. The system updates the ASCII board, tracks the move list, and determines when the game has reached a decisive result.

Administrator Tools

Administrators have access to everything players do, plus:

Creating, editing, or deleting users

Creating and managing tournaments

Starting tournaments and generating pairings

Viewing all users and their statistics

Overseeing tournament standings and participation

Administrative actions follow the same clean layout philosophy, ensuring that even complex tasks remain intuitive.

🧱 Project Structure
Chess_App_Flask/
│
├── app_flask.py            # Main Flask application
├── objects/                # Core data models (User, Game, Move, Tournament)
├── templates/              # HTML/Jinja templates for all views
│   ├── base.html
│   ├── loginbase.html
│   ├── users/
│   ├── tournaments/
│   ├── games/
│   └── ...
│
├── static/
│   └── style.css           # Application styling
│
├── config.yml              # Local database configuration (ignored in Git)
└── README.md               # Project documentation

🚀 Future Improvements

Several enhancements could further strengthen the platform:

Replacing the ASCII board with a graphical chessboard

PGN import/export tools

WebSocket-based live updates

Automatic Elo rating adjustments

Expanded tournament formats (Swiss, round-robin, knockout)

Player avatars and profile customization

Mobile-first UI redesign

These features can be added incrementally without disrupting the current architecture.

🤝 Contributing

Contributions and suggestions are welcome. Whether you want to improve the UI, add new tournament formats, refactor the codebase, or expand gameplay capabilities, feel free to open an issue or submit a pull request.