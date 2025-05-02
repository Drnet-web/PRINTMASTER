import sqlite3
import os

# Percorso del database
DB_PATH = os.path.join(os.path.dirname(__file__), 'db/printmaster.db')

# Connessione al database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Creazione tabella conteggi_mensili
cursor.execute('''
CREATE TABLE IF NOT EXISTS conteggi_mensili (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seriale TEXT NOT NULL,
    anno INTEGER NOT NULL,
    mese INTEGER NOT NULL,
    totale_bn INTEGER,
    totale_colore INTEGER,
    totale_generale INTEGER,
    data_email TEXT,
    note TEXT,
    data_inserimento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seriale) REFERENCES fotocopiatrici(seriale),
    UNIQUE(seriale, anno, mese)
)
''')

conn.commit()
conn.close()
print("Tabella conteggi_mensili creata con successo!")