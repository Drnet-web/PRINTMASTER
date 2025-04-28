import sqlite3
import os

# Percorso del database
db_path = os.path.join(os.path.dirname(__file__), 'db', 'printmaster.db')

# Se la cartella db non esiste, la creo
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Connessione al database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Creazione tabella clienti
cursor.execute('''
CREATE TABLE IF NOT EXISTS clienti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    email TEXT,
    telefono TEXT,
    indirizzo TEXT,
    citta TEXT,
    provincia TEXT,
    cap TEXT
)
''')

# Creazione tabella fotocopiatrici
cursor.execute('''
CREATE TABLE IF NOT EXISTS fotocopiatrici (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seriale TEXT UNIQUE NOT NULL,
    modello TEXT,
    marca TEXT,
    tipologia TEXT,
    colore TEXT,
    cliente_id INTEGER,
    FOREIGN KEY (cliente_id) REFERENCES clienti(id)
)
''')

# Creazione tabella conteggi_stampe
cursor.execute('''
CREATE TABLE IF NOT EXISTS conteggi_stampe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    macchina_id INTEGER,
    mese TEXT,
    copie_bn INTEGER DEFAULT 0,
    copie_colore INTEGER DEFAULT 0,
    FOREIGN KEY (macchina_id) REFERENCES fotocopiatrici(id)
)
''')

conn.commit()
conn.close()

print("Database creato correttamente!")
