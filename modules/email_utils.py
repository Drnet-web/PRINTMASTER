import imaplib
import email
from email.header import decode_header
from bs4 import BeautifulSoup
import re
from email.utils import parsedate_to_datetime

def recupera_email_totali(seriale_filtro=None):
    IMAP_SERVER = "imap.gmail.com"
    EMAIL_ACCOUNT = "roffilli.cristiano@gmail.com"
    PASSWORD = "jzij wavx ybem nsrt"
    
    print("DEBUG - Tentativo di accesso alla mailbox...")

    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    mail.login(EMAIL_ACCOUNT, PASSWORD)
    mail.select("inbox")

    # Ricerca originale senza modifiche
    print("DEBUG - Cercando email da contatori@cdmtecnica.it")
    status, messages = mail.search(None, 'X-GM-RAW "contatori@cdmtecnica.it"')
    ids = messages[0].split()
    print(f"DEBUG - Trovate {len(ids)} email")
    
    results = []

    for mid in ids:
        _, msg_data = mail.fetch(mid, '(RFC822)')
        msg = email.message_from_bytes(msg_data[0][1])
        
        # Stampa informazioni sulla mail per debug
        sender = msg.get('From', 'Unknown')
        subject = msg.get('Subject', 'No Subject')
        date = msg.get('Date', 'Unknown Date')
        print(f"DEBUG - Email: From={sender}, Subject={subject}, Date={date}")
        
        # Estrai la data della mail se possibile
        data_email = None
        try:
            data_email = parsedate_to_datetime(date)
            print(f"DEBUG - Data formattata: {data_email.strftime('%d/%m/%Y')}")
        except:
            print("DEBUG - Impossibile formattare la data")

        # 1) estrai il corpo della mail (text/plain o text/html) per trovare il seriale
        seriale = None
        for part in msg.walk():
            if part.get_content_disposition() is None:
                ctype = part.get_content_type()
                if ctype in ("text/plain", "text/html"):
                    try:
                        text = part.get_payload(decode=True).decode(errors='ignore')
                    except:
                        continue
                    m = re.search(r"Serial(?: Number)?:\s*([A-Za-z0-9\-]+)", text, re.IGNORECASE)
                    if m:
                        seriale = m.group(1)
                        print(f"DEBUG - Seriale trovato: {seriale}")
                        break
        if not seriale:
            print("DEBUG - Nessun seriale trovato, passiamo alla prossima email")
            continue
            
        # Se è stato specificato un seriale di filtro, controlla se corrisponde
        if seriale_filtro and seriale != seriale_filtro:
            print(f"DEBUG - Seriale non corrisponde al filtro: {seriale} != {seriale_filtro}")
            continue

        # 2) cerca l'allegato e ne estrai il totale
        totale_bn = None
        totale_colore = None
        totale_generale = None
        
        for part in msg.walk():
            if part.get_content_disposition() == 'attachment':
                raw_fn = part.get_filename()
                if not raw_fn:
                    continue
                decoded = decode_header(raw_fn)[0][0]
                fn = decoded.decode() if isinstance(decoded, bytes) else decoded
                print(f"DEBUG - Allegato trovato: {fn}")
                
                if fn.lower().endswith('counter_function.htm'):
                    html = part.get_payload(decode=True).decode(errors='ignore')
                    soup = BeautifulSoup(html, 'html.parser')
                    rows = soup.find_all('tr')
                    
                    print(f"DEBUG - Trovate {len(rows)} righe nella tabella")
                    
                    # prendi l'ultima riga "Total"
                    for row in reversed(rows):
                        cols = [td.get_text(strip=True) for td in row.find_all('td')]
                        if len(cols) >= 6 and cols[1].lower() == 'total':
                            print(f"DEBUG - Riga 'Total' trovata: {cols}")
                            try:
                                # Colonna Black & White
                                if cols[2] != '-------':
                                    totale_bn = int(cols[2])
                                
                                # Colonne colore (single + full)
                                totale_colore = 0
                                if cols[3] != '-------':
                                    totale_colore += int(cols[3])  # Single Color
                                if cols[4] != '-------':
                                    totale_colore += int(cols[4])  # Full Color
                                
                                # Total
                                if cols[5] != '-------':
                                    totale_generale = int(cols[5])
                                
                                print(f"DEBUG - Valori estratti: BN={totale_bn}, Colore={totale_colore}, Tot={totale_generale}")
                            except (ValueError, IndexError) as e:
                                print(f"DEBUG - Errore durante l'estrazione dei valori: {e}")
                            break
                    break

        # Aggiungi i risultati
        if totale_bn is not None or totale_colore > 0 or totale_generale is not None:
            results.append({
                'seriale': seriale, 
                'totale_bn': totale_bn,
                'totale_colore': totale_colore if totale_colore > 0 else None,
                'totale_generale': totale_generale,
                'data_email': data_email.strftime('%d/%m/%Y') if data_email else 'Data sconosciuta'
            })
            print(f"DEBUG - Risultato aggiunto per seriale {seriale}")

    mail.logout()
    print(f"DEBUG - Totale risultati trovati: {len(results)}")
    return results