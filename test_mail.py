import imaplib
import email
from email.header import decode_header

# Dati di accesso
EMAIL_ACCOUNT = "roffillicristiano@gmail.com"  # Sostituisci con il tuo indirizzo email
PASSWORD = "jzij wavx ybem nsrt"  # Sostituisci con la password per l'app generata

# Configura il server IMAP (Outlook/Hotmail in questo caso)
IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993  # Porta IMAP con SSL

try:
    # Connessione al server IMAP
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    
    # Login al server con le credenziali
    mail.login(EMAIL_ACCOUNT, PASSWORD)
    print("Login riuscito!")

    # Se il login è riuscito, prova a selezionare la casella "INBOX"
    mail.select("inbox")  # Seleziona la casella di posta "INBOX"

    # Cerca tutte le email nella casella di posta
    status, messages = mail.search(None, 'ALL')
    if status == "OK":
        # Stampa il numero di email trovate
        print(f"Trovate {len(messages[0].split())} email nella casella INBOX.")
    else:
        print("Errore nella ricerca delle email.")

except imaplib.IMAP4.error as e:
    print(f"Errore di login: {e}")

finally:
    # Chiudi la connessione
    if mail:
        mail.logout()
