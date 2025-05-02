import sqlite3
import os

# Percorso del database
DB_PATH = os.path.join(os.path.dirname(__file__), 'db/printmaster.db')

def migrate_database():
    """Aggiorna il database con le tabelle necessarie"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 1. Verifica se la tabella prospetti_affitti esiste già
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='prospetti_affitti'
        """)
        if not cursor.fetchone():
            print("Creazione tabella prospetti_affitti...")
            cursor.execute("""
                CREATE TABLE prospetti_affitti (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_locatario INTEGER,
                    id_stampante INTEGER,
                    mese_rif INTEGER,
                    anno_rif INTEGER,
                    totale_copie_bw INTEGER,
                    totale_copie_colore INTEGER,
                    data_generazione DATETIME,
                    FOREIGN KEY (id_locatario) REFERENCES clienti(id),
                    FOREIGN KEY (id_stampante) REFERENCES fotocopiatrici(id)
                )
            """)
            print("Tabella prospetti_affitti creata con successo!")
        else:
            print("Tabella prospetti_affitti già esistente.")
        
        # 2. Verifica se la tabella conteggi_stampe esiste già
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='conteggi_stampe'
        """)
        if not cursor.fetchone():
            print("Creazione tabella conteggi_stampe...")
            cursor.execute("""
                CREATE TABLE conteggi_stampe (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    id_prospetto_affitti INTEGER,
                    data_generazione DATETIME,
                    percorso_file TEXT,
                    mese_periodo TEXT,
                    copie_nero_periodo INTEGER,
                    copie_colore_periodo INTEGER,
                    note TEXT,
                    FOREIGN KEY (id_prospetto_affitti) REFERENCES prospetti_affitti(id)
                )
            """)
            print("Tabella conteggi_stampe creata con successo!")
        else:
            # Se esiste già, verifica che abbia tutti i campi necessari
            print("Verifica struttura tabella conteggi_stampe...")
            cursor.execute("PRAGMA table_info(conteggi_stampe)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # Verifica se mancano colonne e aggiungile se necessario
            columns_to_add = {
                'mese_periodo': 'TEXT',
                'copie_nero_periodo': 'INTEGER',
                'copie_colore_periodo': 'INTEGER'
            }
            
            for col_name, col_type in columns_to_add.items():
                if col_name not in columns:
                    print(f"Aggiunta colonna {col_name}...")
                    cursor.execute(f"ALTER TABLE conteggi_stampe ADD COLUMN {col_name} {col_type}")
                    print(f"Colonna {col_name} aggiunta con successo!")
        
        # 3. Crea la struttura delle cartelle se non esiste
        base_path = 'print_master/prospetti/'
        if not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)
            print(f"Creata struttura cartelle: {base_path}")
        
        conn.commit()
        print("\nMigrazione completata con successo!")
        
    except Exception as e:
        print(f"Errore durante la migrazione: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

# Funzione per verificare la struttura attuale
def check_database_structure():
    """Verifica la struttura attuale del database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=== STRUTTURA DATABASE ATTUALE ===\n")
    
    # Lista tutte le tabelle
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        print(f"Tabella: {table_name}")
        
        # Mostra le colonne di ogni tabella
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        print("Colonne:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        print()
    
    conn.close()

if __name__ == "__main__":
    print("Script di migrazione database PrintMaster\n")
    
    # Verifica struttura attuale
    print("1. Verifica struttura database attuale:")
    check_database_structure()
    
    # Chiedi conferma per procedere
    risposta = input("\nVuoi procedere con la migrazione? (s/n): ")
    if risposta.lower() == 's':
        print("\n2. Esecuzione migrazione:")
        migrate_database()
        
        print("\n3. Verifica struttura dopo migrazione:")
        check_database_structure()
    else:
        print("Migrazione annullata.")