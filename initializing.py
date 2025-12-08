import yaml
import pymysql

with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

dbconf = config["db"]

conn = pymysql.connect(
    host=dbconf.get("host", "localhost"),
    port=dbconf.get("port", 3306),
    user=dbconf["user"],
    passwd=dbconf["pw"],
    db=dbconf["db"],
    autocommit=True
)



cur = conn.cursor(pymysql.cursors.DictCursor)


cur.execute('''
    CREATE TABLE IF NOT EXISTS chess_users (
    userKey      INT AUTO_INCREMENT PRIMARY KEY,
    userID       VARCHAR(50)  NOT NULL,   
    Fname        VARCHAR(50)  NOT NULL,
    Lname        VARCHAR(50)  NOT NULL,
    password VARCHAR(255) NOT NULL,
    email        VARCHAR(100) NOT NULL,
    country      VARCHAR(3),
    DOB          DATE,
    rating       INT,
    title        VARCHAR(10),            
    role         VARCHAR(20),            
    UNIQUE KEY uq_chess_users_userID (userID),
    UNIQUE KEY uq_chess_users_email  (email)
)   ''')



cur.execute('''
    CREATE TABLE IF NOT EXISTS chess_tournaments (
    tournamentKey  INT AUTO_INCREMENT PRIMARY KEY,
    tournamentID   VARCHAR(50) NOT NULL,  
    name           VARCHAR(100) NOT NULL,
    location       VARCHAR(100),
    ratingLimit    INT,                   
    personLimit    INT,

    UNIQUE KEY uq_chess_tournaments_tournamentID (tournamentID)
);           

    ''')


cur.execute('''ALTER TABLE chess_tournaments
ADD COLUMN winnerKey INT NULL;
            ''')


cur.execute('''
    CREATE TABLE IF NOT EXISTS chess_games (
    gameKey       INT AUTO_INCREMENT PRIMARY KEY,
    gameID        VARCHAR(50) NOT NULL,  
    result        VARCHAR(7) NOT NULL,  
    date          DATE,
    tournamentKey INT,                   
    whiteKey      INT,                  
    blackKey      INT,                   
            
    UNIQUE KEY uq_chess_games_gameID (gameID),
    KEY idx_chess_games_tournamentKey (tournamentKey),
    KEY idx_chess_games_whiteKey      (whiteKey),
    KEY idx_chess_games_blackKey      (blackKey),

    CONSTRAINT fk_chess_games_tournament
        FOREIGN KEY (tournamentKey)
        REFERENCES chess_tournaments (tournamentKey)
        ON UPDATE CASCADE ON DELETE SET NULL,

    CONSTRAINT fk_chess_games_white
        FOREIGN KEY (whiteKey)
        REFERENCES chess_users (userKey)
        ON UPDATE CASCADE ON DELETE SET NULL,

    CONSTRAINT fk_chess_games_black
        FOREIGN KEY (blackKey)
        REFERENCES chess_users (userKey)
        ON UPDATE CASCADE ON DELETE SET NULL

); ''')



cur.execute('''
ALTER TABLE chess_games
ADD COLUMN round INT NULL;
            ''')

cur.execute('''
    CREATE TABLE IF NOT EXISTS chess_moves (
        moveKey       INT AUTO_INCREMENT PRIMARY KEY,
        move          VARCHAR(250) NOT NULL,
        madeBy        VARCHAR(3) NOT NULL,
        evalAfter     DECIMAL(6,2),
        elapsedTime   INT,
        gameKey       INT NOT NULL,
            
    KEY idx_chess_moves_gameKey (gameKey),

    CONSTRAINT fk_chess_moves_game
        FOREIGN KEY (gameKey)
        REFERENCES chess_games (gameKey)
        ON UPDATE CASCADE ON DELETE CASCADE

            );
    ''')


cur.execute('''
CREATE TABLE tournamentEntry (
    entryKey      INT AUTO_INCREMENT PRIMARY KEY,
    tournamentKey INT NOT NULL,
    userKey       INT NOT NULL,
            
    UNIQUE KEY uq_entry_tournament_user (tournamentKey, userKey),


    CONSTRAINT fk_entry_tournament
        FOREIGN KEY (tournamentKey) REFERENCES chess_tournaments(tournamentKey)
        ON UPDATE CASCADE ON DELETE CASCADE,

    CONSTRAINT fk_entry_user
        FOREIGN KEY (userKey) REFERENCES chess_users(userKey)
        ON UPDATE CASCADE ON DELETE CASCADE
);
  ''')

cur.execute('''
INSERT INTO chess_users
(userID, Fname, Lname, email, password, country, DOB, rating, title, role)
VALUES
('tal01',    'Mikhail',  'Tal',      'tal@chess.com',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'LAT',  '1936-11-09', 2705, 'GM', 'player'),

('toni01',    'Toni',  'Crnjak',      'tc@admin',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'CRO',  '1998-01-26', 1405, '', 'admin'),

('fischer',  'Bobby',    'Fischer',  'fischer@chess.com',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'USA',     '1943-03-09', 2785, 'GM', 'player'),

('kasparov', 'Garry',    'Kasparov', 'kasparov@chess.com',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'RUS',  '1963-04-13', 2851, 'GM', 'player'),

('karpov',   'Anatoly',  'Karpov',   'karpov@chess.com',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'RUS',  '1951-05-23', 2720, 'GM', 'player'),

('carlsen',  'Magnus',   'Carlsen',  'carlsen@chess.com',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'NOR',  '1990-11-30', 2882, 'GM', 'player'),

('hikaru',   'Hikaru',   'Nakamura', 'hikaru@chess.com',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'USA',     '1987-12-09', 2780, 'GM', 'player'),

('lazo',     'Lazar',     'Rokvic',   'lrokvic@chess.edu',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'CRO',     '2001-03-15', 2100, 'NM', 'player'),

('judit',    'Judit',    'Polgar',   'judit@chess.com',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'HUN', '1976-07-23', 2735, 'GM', 'player'),
            
('p001', 'Player1', 'Test', 'p001@chess.test',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'POL', '1994-07-02', 1330, 'NM', 'player'),

('p002', 'Player2', 'Test', 'p002@chess.test',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'GER', '1995-05-16', 1533, 'NM', 'player'),

('p003', 'Player3', 'Test', 'p003@chess.test',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'UKR', '1983-09-05', 1377, 'GM', 'player'),

('p004', 'Player4', 'Test', 'p004@chess.test',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'NED', '1976-10-26', 1313, 'NM', 'player'),

('p005', 'Player5', 'Test', 'p005@chess.test',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'ITA', '2008-03-10', 1002, 'CM', 'player'),

('p006', 'Player6', 'Test', 'p006@chess.test',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'NED', '1981-01-09', 2104, 'GM', 'player'),

('p007', 'Player7', 'Test', 'p007@chess.test',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'GER', '1986-11-26', 1322, '', 'player'),

('p008', 'Player8', 'Test', 'p008@chess.test',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'ESP', '1973-06-12', 2136, 'FM', 'player'),

('p009', 'Player9', 'Test', 'p009@chess.test',
 'adf47922f0bdb6b9a520ed2d43622d14',
 'FRA', '1989-12-24', 1737, 'GM', 'player');
            ''')


cur.execute('''
INSERT INTO chess_tournaments
(tournamentID, name, location, ratingLimit, personLimit)
VALUES
('candidates59', 'Candidates Tournament 1959', 'Bled/Zagreb/Belgrade', 2800, 8),
('wc1972',       'World Championship 1972',    'Reykjavik',            2800, 2),
('wc1985',       'World Championship 1985',    'Moscow',               2800, 2),
('norway2024',   'Norway Chess 2024',         'Stavanger',            2900, 10),
('us_open',      'US Open Championship',       'St. Louis',            2700, 50),
('test1',      'class1',       'Potsdam', 1000, 4),
('test2',      'class3',       'Potsdam', 1000, 8),
('test3',      'class2',       'Potsdam', 1000, 16);

            ''')

cur.execute('''
INSERT INTO chess_games
(gameID, date, tournamentKey, whiteKey, blackKey, result)
VALUES
('g1_tal_fischer',   '1959-09-10',5 , 1, 2, '1-0'),
('g2_fischer_tal',   '1959-09-20',5 , 2, 1, '0-1'),
('g3_kas_karpov',    '1985-10-01',5 , 3, 4, '1-0'),
('g4_karpov_kas',    '1985-10-15',5 , 4, 3, '0-1'),
('g5_fischer_spare', '1972-07-11',5 , 2, 3, '1-0'),
('g6_carlsen_hik',   '2024-06-05',5 , 5, 6, '0.5-0.5'),
('g7_hik_carlsen',   '2024-06-07',5 , 6, 5, '1-0'),
('g10_lazo_hikaru',  '2025-01-20',5 , 7, 6, '0-1');
''')


cur.execute('''
 INSERT INTO chess_moves (move, madeBy, evalAfter, elapsedTime, gameKey) VALUES
('e4',     'W', 0.00, 60, 1),
('c5',     'B', 0.00, 60, 1),
('Nf3',    'W', 0.00, 60, 1),
('Nc6',    'B', 0.00, 60, 1),
('d4',     'W', 0.00, 60, 1),
('cxd4',   'B', 0.00, 60, 1),
('Nxd4',   'W', 0.00, 60, 1),
('e6',     'B', 0.00, 60, 1),
('Nc3',    'W', 0.00, 60, 1),
('Qc7',    'B', 0.00, 60, 1),
('g3',     'W', 0.00, 60, 1),
('Nf6',    'B', 0.00, 60, 1),
('Ndb5',   'W', 0.00, 60, 1),
('Qb8',    'B', 0.00, 60, 1),
('Bf4',    'W', 0.00, 60, 1),
('Ne5',    'B', 0.00, 60, 1),
('Be2',    'W', 0.00, 60, 1),
('Bc5',    'B', 0.00, 60, 1),
('Bxe5',   'W', 0.00, 60, 1),
('Qxe5',   'B', 0.00, 60, 1),
('f4',     'W', 0.00, 60, 1),
('Qb8',    'B', 0.00, 60, 1),
('e5',     'W', 0.00, 60, 1),
('a6',     'B', 0.00, 60, 1),
('exf6',   'W', 0.00, 60, 1),
('axb5',   'B', 0.00, 60, 1),
('fxg7',   'W', 0.00, 60, 1),
('Rg8',    'B', 0.00, 60, 1),
('Ne4',    'W', 0.00, 60, 1),
('Be7',    'B', 0.00, 60, 1),
('Qd4',    'W', 0.00, 60, 1),
('Ra4',    'B', 0.00, 60, 1),
('Nf6+',   'W', 0.00, 60, 1),
('Bxf6',   'B', 0.00, 60, 1),
('Qxf6',   'W', 0.00, 60, 1),
('Qc7',    'B', 0.00, 60, 1),
('O-O-O',  'W', 0.00, 60, 1),
('Rxa2',   'B', 0.00, 60, 1),
('Kb1',    'W', 0.00, 60, 1),
('Ra6',    'B', 0.00, 60, 1),
('Bxb5',   'W', 0.00, 60, 1),
('Rb6',    'B', 0.00, 60, 1),
('Bd3',    'W', 0.00, 60, 1),
('e5',     'B', 0.00, 60, 1),
('fxe5',   'W', 0.00, 60, 1),
('Rxf6',   'B', 0.00, 60, 1),
('exf6',   'W', 0.00, 60, 1),
('Qc5',    'B', 0.00, 60, 1),
('Bxh7',   'W', 0.00, 60, 1),
('Qg5',    'B', 0.00, 60, 1),
('Bxg8',   'W', 0.00, 60, 1),
('Qxf6',   'B', 0.00, 60, 1),
('Rhf1',   'W', 0.00, 60, 1),
('Qxg7',   'B', 0.00, 60, 1),
('Bxf7+',  'W', 0.00, 60, 1),
('Kd8',    'B', 0.00, 60, 1),
('Be6',    'W', 0.00, 60, 1),
('Qh6',    'B', 0.00, 60, 1),
('Bxd7',   'W', 0.00, 60, 1),
('Bxd7',   'B', 0.00, 60, 1),
('Rf7',    'W', 0.00, 60, 1),
('Qxh2',   'B', 0.00, 60, 1),
('Rdxd7+', 'W', 0.00, 60, 1),
('Ke8',    'B', 0.00, 60, 1),
('Rde7+',  'W', 0.00, 60, 1),
('Kd8',    'B', 0.00, 60, 1),
('Rd7+',   'W', 0.00, 60, 1),
('Kc8',    'B', 0.00, 60, 1),
('Rc7+',   'W', 0.00, 60, 1),
('Kd8',    'B', 0.00, 60, 1),
('Rfd7+',  'W', 0.00, 60, 1),
('Ke8',    'B', 0.00, 60, 1),
('Rd1',    'W', 0.00, 60, 1),
('b5',     'B', 0.00, 60, 1),
('Rb7',    'W', 0.00, 60, 1),
('Qh5',    'B', 0.00, 60, 1),
('g4',     'W', 0.00, 60, 1),
('Qh3',    'B', 0.00, 60, 1),
('g5',     'W', 0.00, 60, 1),
('Qf3',    'B', 0.00, 60, 1),
('Re1+',   'W', 0.00, 60, 1),
('Kf8',    'B', 0.00, 60, 1),
('Rxb5',   'W', 0.00, 60, 1),
('Kg7',    'B', 0.00, 60, 1),
('Rb6',    'W', 0.00, 60, 1),
('Qg3',    'B', 0.00, 60, 1),
('Rd1',    'W', 0.00, 60, 1),
('Qc7',    'B', 0.00, 60, 1),
('Rdd6',   'W', 0.00, 60, 1),
('Qc8',    'B', 0.00, 60, 1),
('b3',     'W', 0.00, 60, 1),
('Kh7',    'B', 0.00, 60, 1),
('Ra6',    'W', 0.00, 60, 1),
('d4',  'W', 0.10, 60,  6),
('Nf6', 'B', 0.05, 55,  6),
('c4',  'W', 0.20, 70,  6),
('g6',  'B', 0.15, 65,  6),
('Nc3', 'W', 0.25, 80,  6),
('Bg7', 'B', 0.20, 75,  6),
('e4',  'W', 0.05, 45,  8),
('c5',  'B', 0.00, 50,  8),
('Nf3', 'W', 0.10, 40,  8),
('d6',  'B', 0.05, 55,  8),
('d4',  'W', 0.20, 70,  8),
('cxd4','B', 0.15, 65,  8);
            ''')

cur.execute('''
INSERT INTO tournamentEntry (tournamentKey, userKey)
SELECT t.tournamentKey, u.userKey
FROM chess_tournaments t
JOIN chess_users u ON u.userID IN (
    'carlsen',
    'hikaru',
    'fischer',
    'kasparov'
)
WHERE t.tournamentID = 'test1';
''')

cur.execute('''
INSERT INTO tournamentEntry (tournamentKey, userKey)
SELECT t.tournamentKey, u.userKey
FROM chess_tournaments t
JOIN chess_users u ON u.userID IN (
    'tal01',
    'karpov',
    'judit',
    'lazo',
    'p001',
    'p002',
    'p003',
    'p004'
)
WHERE t.tournamentID = 'test2';
''')

cur.execute('''
INSERT INTO tournamentEntry (tournamentKey, userKey)
SELECT t.tournamentKey, u.userKey
FROM chess_tournaments t
JOIN chess_users u ON u.userID IN (
    'p005',
    'p006',
    'p007',
    'p008',
    'p009',
    'p010',
    'p011',
    'p012',
    'p013',
    'p014',
    'p015',
    'p016',
    'p017',
    'p018',
    'p019',
    'p020'
)
WHERE t.tournamentID = 'test3';
''')

conn.commit()




