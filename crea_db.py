import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(__file__), 'db')
DB_PATH = os.path.join(DB_DIR, 'printmaster.db')

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Creazione tabella clienti
cursor.execute('''
CREATE TABLE IF NOT EXISTS clienti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    indirizzo TEXT NOT NULL,
    citta TEXT NOT NULL,
    cap TEXT NOT NULL,
    provincia TEXT NOT NULL,
    email TEXT,
    telefono TEXT
)
''')

# Creazione tabella fotocopiatrici
cursor.execute('''
CREATE TABLE IF NOT EXISTS fotocopiatrici (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seriale TEXT NOT NULL UNIQUE,
    modello TEXT NOT NULL,
    marca TEXT NOT NULL,
    tipologia TEXT NOT NULL,
    colore TEXT NOT NULL,
    cliente_id INTEGER NOT NULL,
    forfait_nero INTEGER NOT NULL DEFAULT 0,
    forfait_colore INTEGER NOT NULL DEFAULT 0,
    costo_copia_nero REAL NOT NULL DEFAULT 0,
    costo_copia_colore REAL NOT NULL DEFAULT 0,
    FOREIGN KEY (cliente_id) REFERENCES clienti(id)
)
''')

# Creazione tabella conteggi_stampe
cursor.execute('''
CREATE TABLE IF NOT EXISTS conteggi_stampe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fotocopiatrice_id INTEGER NOT NULL,
    periodo TEXT NOT NULL,
    copie_nero INTEGER NOT NULL DEFAULT 0,
    copie_colore INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (fotocopiatrice_id) REFERENCES fotocopiatrici(id)
)
''')

conn.commit()
conn.close()

print("Database creato correttamente con tutte le tabelle!")
