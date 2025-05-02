from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for, send_file
import sqlite3
import os
from datetime import datetime
from modules.email_utils import recupera_email_totali
from fpdf import FPDF


conteggi_bp = Blueprint('conteggi', __name__)
DB_PATH = os.path.join(os.path.dirname(__file__), '../db/printmaster.db')

def salva_conteggio_mensile(seriale, totale_bn, totale_colore, totale_generale, data_email):
    """Salva il conteggio mensile nel database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Estrai anno e mese dalla data dell'email
        if data_email != 'Data sconosciuta':
            # Assumendo che data_email sia nel formato dd/mm/yyyy
            giorno, mese, anno = map(int, data_email.split('/'))
        else:
            # Se non abbiamo la data, usiamo la data corrente
            now = datetime.now()
            anno = now.year
            mese = now.month
        
        # Prova a inserire o aggiornare se esiste già
        cursor.execute('''
            INSERT OR REPLACE INTO conteggi_mensili 
            (seriale, anno, mese, totale_bn, totale_colore, totale_generale, data_email)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (seriale, anno, mese, totale_bn, totale_colore, totale_generale, data_email))
        
        conn.commit()
        return True, f"Conteggio salvato per {mese}/{anno}"
    except Exception as e:
        return False, f"Errore nel salvataggio: {str(e)}"
    finally:
        conn.close()

def recupera_conteggio_precedente(seriale, anno, mese):
    """Recupera il conteggio del mese precedente per un dato seriale"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Calcola il mese precedente
        if mese == 1:
            mese_precedente = 12
            anno_precedente = anno - 1
        else:
            mese_precedente = mese - 1
            anno_precedente = anno
        
        # Recupera il conteggio del mese precedente
        cursor.execute('''
            SELECT totale_bn, totale_colore, totale_generale 
            FROM conteggi_mensili 
            WHERE seriale = ? AND anno = ? AND mese = ?
        ''', (seriale, anno_precedente, mese_precedente))
        
        risultato = cursor.fetchone()
        
        if risultato:
            return {
                'totale_bn': risultato[0],
                'totale_colore': risultato[1],
                'totale_generale': risultato[2]
            }
        else:
            # Se non trova il mese precedente, restituisce None
            return None
    except Exception as e:
        print(f"Errore nel recupero del conteggio precedente: {str(e)}")
        return None
    finally:
        conn.close()

def calcola_eccedenze(seriale, anno, mese, totale_bn_attuale, totale_colore_attuale):
    """Calcola le eccedenze rispetto ai forfait"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Recupera i forfait e i costi dalla tabella fotocopiatrici
        cursor.execute('''
            SELECT forfait_nero, forfait_colore, costo_copia_nero, costo_copia_colore 
            FROM fotocopiatrici 
            WHERE seriale = ?
        ''', (seriale,))
        
        dati_forfait = cursor.fetchone()
        if not dati_forfait:
            return None
        
        forfait_nero, forfait_colore, costo_copia_nero, costo_copia_colore = dati_forfait
        
        # Recupera il conteggio del mese precedente
        conteggio_precedente = recupera_conteggio_precedente(seriale, anno, mese)
        
        if conteggio_precedente:
            # Calcola le differenze rispetto al mese precedente
            differenza_bn = totale_bn_attuale - (conteggio_precedente['totale_bn'] or 0)
            differenza_colore = totale_colore_attuale - (conteggio_precedente['totale_colore'] or 0)
        else:
            # Se non c'è un mese precedente, usa i totali attuali
            differenza_bn = totale_bn_attuale
            differenza_colore = totale_colore_attuale
        
        # Calcola le eccedenze
        eccedenza_bn = max(0, differenza_bn - forfait_nero)
        eccedenza_colore = max(0, differenza_colore - forfait_colore)
        
        # Calcola i costi
        costo_eccedenza_bn = eccedenza_bn * costo_copia_nero
        costo_eccedenza_colore = eccedenza_colore * costo_copia_colore
        totale_costo = costo_eccedenza_bn + costo_eccedenza_colore
        
        return {
            'differenza_bn': differenza_bn,
            'differenza_colore': differenza_colore,
            'forfait_nero': forfait_nero,
            'forfait_colore': forfait_colore,
            'eccedenza_bn': eccedenza_bn,
            'eccedenza_colore': eccedenza_colore,
            'costo_copia_nero': costo_copia_nero,
            'costo_copia_colore': costo_copia_colore,
            'costo_eccedenza_bn': costo_eccedenza_bn,
            'costo_eccedenza_colore': costo_eccedenza_colore,
            'totale_costo': totale_costo,
            'mese_precedente_trovato': conteggio_precedente is not None
        }
    except Exception as e:
        print(f"Errore nel calcolo delle eccedenze: {str(e)}")
        return None
    finally:
        conn.close()

@conteggi_bp.route('/', methods=['GET', 'POST'])
def conteggi():
    # Carica solo i clienti inizialmente
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Recupera tutti i clienti
    cursor.execute('SELECT id, nome FROM clienti ORDER BY nome')
    clienti = cursor.fetchall()
    
    # Variabili per i risultati
    totale_bn = None
    totale_colore = None
    totale_generale = None
    seriale_estratto = None
    tipo_macchina = None
    cliente_selezionato = None
    seriale_selezionato = None
    fotocopiatrici_cliente = []
    data_email = None
    eccedenze = None  # NUOVA VARIABILE
    pdf_path_download = None  # NUOVA VARIABILE per il PDF
    
    # Gestione del form quando inviato
    if request.method == 'POST':
        # Ottieni il cliente selezionato
        cliente_selezionato = request.form.get('cliente_id')
        seriale_selezionato = request.form.get('seriale')
        
        # Se abbiamo un cliente, carica le sue fotocopiatrici
        if cliente_selezionato:
            cursor.execute('''
                SELECT id, seriale, modello, marca
                FROM fotocopiatrici
                WHERE cliente_id = ?
                ORDER BY seriale
            ''', (cliente_selezionato,))
            
            fotocopiatrici = cursor.fetchall()
            fotocopiatrici_cliente = []
            for f in fotocopiatrici:
                fotocopiatrici_cliente.append({
                    'id': f[0],
                    'seriale': f[1],
                    'modello': f[2],
                    'marca': f[3],
                    'display_name': f"{f[1]} - {f[2]} {f[3]}"
                })
        
        # Se stiamo cercando i conteggi
        if request.form.get('action') == 'recupera_email' and seriale_selezionato:
            # Prima controlla il tipo di fotocopiatrice (colore o bianco/nero)
            try:
                cursor.execute('''
                    SELECT colore FROM fotocopiatrici 
                    WHERE seriale = ?
                ''', (seriale_selezionato,))
                tipo_macchina = cursor.fetchone()
                if tipo_macchina:
                    tipo_macchina = tipo_macchina[0]  # "Si" o "No" per il colore
            except:
                tipo_macchina = None
            
            # Cerca l'ultima email per il seriale selezionato
            results = recupera_email_totali(seriale_filtro=seriale_selezionato)
            
            if results:
                # prendo il primo risultato
                seriale_estratto = results[0]['seriale']
                totale_bn = results[0]['totale_bn']
                totale_colore = results[0]['totale_colore']
                totale_generale = results[0].get('totale_generale')
                data_email = results[0].get('data_email', 'Data sconosciuta')
                
                # Salva automaticamente i dati nel database
                success, message = salva_conteggio_mensile(
                    seriale_estratto, 
                    totale_bn, 
                    totale_colore, 
                    totale_generale, 
                    data_email
                )
        
                if success:
                    flash(message, "success")
                    
                    # NUOVO: Calcola automaticamente le eccedenze dopo il salvataggio
                    if data_email != 'Data sconosciuta':
                        giorno, mese, anno = map(int, data_email.split('/'))
                        eccedenze = calcola_eccedenze(
                            seriale_estratto, 
                            anno, 
                            mese, 
                            totale_bn or 0, 
                            totale_colore or 0
                        )
                        
                        # NUOVO: Genera il PDF
                        # Recupera il nome del cliente
                        cursor.execute('SELECT nome FROM clienti WHERE id = ?', (cliente_selezionato,))
                        cliente_nome = cursor.fetchone()[0]
                        
                        # Genera il PDF
                        pdf_path, pdf_filename = genera_pdf_prospetto(
                            seriale_estratto,
                            cliente_nome,
                            totale_bn,
                            totale_colore,
                            eccedenze,
                            data_email
                        )
                        
                        # Registra il PDF nella tabella con l'id del cliente
                        if registra_pdf_generato(seriale_estratto, pdf_path, mese, anno, totale_bn or 0, totale_colore or 0, cliente_selezionato):
                            flash(f"PDF generato: {pdf_filename}", "info")
                            pdf_path_download = pdf_path  # Imposta il percorso per il download
                        else:
                            flash("Errore nella registrazione del PDF", "warning")
                else:
                    flash(message, "warning")
                
                # Ricarica le fotocopiatrici dopo il salvataggio
                if cliente_selezionato:
                    cursor.execute('''
                        SELECT id, seriale, modello, marca
                        FROM fotocopiatrici
                        WHERE cliente_id = ?
                        ORDER BY seriale
                    ''', (cliente_selezionato,))
                    
                    fotocopiatrici = cursor.fetchall()
                    fotocopiatrici_cliente = []
                    for f in fotocopiatrici:
                        fotocopiatrici_cliente.append({
                            'id': f[0],
                            'seriale': f[1],
                            'modello': f[2],
                            'marca': f[3],
                            'display_name': f"{f[1]} - {f[2]} {f[3]}"
                        })
            else:
                flash(f"Nessuna email trovata per il seriale {seriale_selezionato}.", "warning")
    
    conn.close()
    return render_template(
        'conteggi.html',
        clienti=clienti,
        totale_bn=totale_bn,
        totale_colore=totale_colore,
        totale_generale=totale_generale,
        seriale_estratto=seriale_estratto,
        tipo_macchina=tipo_macchina,
        cliente_selezionato=cliente_selezionato,
        seriale_selezionato=seriale_selezionato,
        fotocopiatrici_cliente=fotocopiatrici_cliente,
        data_email=data_email,
        eccedenze=eccedenze,  # NUOVA VARIABILE
        pdf_path_download=pdf_path_download  # NUOVA VARIABILE per il PDF
    )

# Nuova route per caricare le fotocopiatrici di un cliente
@conteggi_bp.route('/get_fotocopiatrici/<int:cliente_id>', methods=['GET'])
def get_fotocopiatrici(cliente_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, seriale, modello, marca
        FROM fotocopiatrici
        WHERE cliente_id = ?
        ORDER BY seriale
    ''', (cliente_id,))
    
    fotocopiatrici = cursor.fetchall()
    conn.close()
    
    # Formatta i dati per la risposta JSON
    result = []
    for f in fotocopiatrici:
        result.append({
            'id': f[0],
            'seriale': f[1],
            'modello': f[2],
            'marca': f[3],
            'display_name': f"{f[1]} - {f[2]} {f[3]}"
        })
    
    return jsonify(result)
    
@conteggi_bp.route('/download/<path:filename>')
def download_pdf(filename):
    """Route per il download dei PDF generati"""
    from flask import send_file
    try:
        return send_file(filename, as_attachment=True)
    except Exception as e:
        flash(f"Errore nel download del file: {str(e)}", "danger")
        return redirect(url_for('conteggi.conteggi'))    
    
    
def genera_pdf_prospetto(seriale, cliente_nome, totale_bn, totale_colore, eccedenze, data_email):
    """Genera il PDF del prospetto e lo salva nella struttura corretta"""
    
    # Estrai mese e anno dalla data email
    if data_email != 'Data sconosciuta':
        giorno, mese, anno = map(int, data_email.split('/'))
    else:
        now = datetime.now()
        mese = now.month
        anno = now.year
    
    # Crea la struttura delle cartelle
    base_path = 'print_master/prospetti/'
    year_path = os.path.join(base_path, str(anno))
    month_path = os.path.join(year_path, f'{mese:02d}')
    
    # Crea le cartelle se non esistono
    os.makedirs(month_path, exist_ok=True)
    
    # Nome del file
    cliente_nome_clean = cliente_nome.lower().replace(' ', '_')
    filename = f"prospetto_{cliente_nome_clean}_{mese:02d}_{anno}.pdf"
    filepath = os.path.join(month_path, filename)
    
    # Genera il PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Intestazione
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'PROSPETTO COPIE ECCEDENTI', 0, 1, 'C')
    pdf.ln(10)
    
    # Info cliente e periodo
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'Cliente: {cliente_nome}', 0, 1)
    pdf.cell(0, 10, f'Seriale: {seriale}', 0, 1)
    mesi = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 
            'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
    pdf.cell(0, 10, f'Periodo: {mesi[mese-1]} {anno}', 0, 1)
    pdf.ln(10)
    
    # Tabella conteggi
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(100, 8, 'Descrizione', 1, 0, 'C')
    pdf.cell(45, 8, 'B/N', 1, 0, 'C')
    pdf.cell(45, 8, 'Colore', 1, 1, 'C')
    
    pdf.set_font('Arial', '', 11)
    # Conteggi totali
    pdf.cell(100, 8, 'Totale Stampe', 1, 0)
    pdf.cell(45, 8, str(totale_bn or 0), 1, 0, 'C')
    pdf.cell(45, 8, str(totale_colore or 0), 1, 1, 'C')
    
    if eccedenze:
        # Stampe nel periodo
        pdf.cell(100, 8, 'Stampe nel periodo', 1, 0)
        pdf.cell(45, 8, str(eccedenze['differenza_bn']), 1, 0, 'C')
        pdf.cell(45, 8, str(eccedenze['differenza_colore']), 1, 1, 'C')
        
        # Forfait
        pdf.cell(100, 8, 'Forfait incluso', 1, 0)
        pdf.cell(45, 8, str(eccedenze['forfait_nero']), 1, 0, 'C')
        pdf.cell(45, 8, str(eccedenze['forfait_colore']), 1, 1, 'C')
        
        # Eccedenze
        pdf.cell(100, 8, 'Copie eccedenti', 1, 0)
        pdf.cell(45, 8, str(eccedenze['eccedenza_bn']), 1, 0, 'C')
        pdf.cell(45, 8, str(eccedenze['eccedenza_colore']), 1, 1, 'C')
        
        # Costi unitari
        pdf.cell(100, 8, 'Costo per copia', 1, 0)
        pdf.cell(45, 8, f"EUR {eccedenze['costo_copia_nero']:.4f}", 1, 0, 'C')
        pdf.cell(45, 8, f"EUR {eccedenze['costo_copia_colore']:.4f}", 1, 1, 'C')
        
        # Totali
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(100, 8, 'Totale Eccedenze', 1, 0)
        pdf.cell(45, 8, f"EUR {eccedenze['costo_eccedenza_bn']:.2f}", 1, 0, 'C')
        pdf.cell(45, 8, f"EUR {eccedenze['costo_eccedenza_colore']:.2f}", 1, 1, 'C')
        
        # Totale da fatturare
        pdf.cell(100, 8, 'TOTALE DA FATTURARE', 1, 0, 'C')
        pdf.cell(90, 8, f"EUR {eccedenze['totale_costo']:.2f}", 1, 1, 'C')
    
    # Salva il PDF
    pdf.output(filepath)
    
    return filepath, filename
    
def registra_pdf_generato(seriale, filepath, mese, anno, totale_bn, totale_colore, cliente_id):
    """Registra il PDF generato nella tabella conteggi_stampe"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Trova l'id della fotocopiatrice dal seriale
        cursor.execute('SELECT id FROM fotocopiatrici WHERE seriale = ?', (seriale,))
        stampante_result = cursor.fetchone()
        if not stampante_result:
            return False
        id_stampante = stampante_result[0]
        
        # Registra nella tabella conteggi_stampe
        mesi = ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 
                'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre']
        periodo = f"{mesi[mese-1]} {anno}"
        
        # Insert usando le colonne corrette
        cursor.execute('''
            INSERT INTO conteggi_stampe 
            (fotocopiatrice_id, periodo, copie_nero, copie_colore, mese_periodo, copie_nero_periodo, copie_colore_periodo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (id_stampante, periodo, totale_bn, totale_colore, periodo, totale_bn, totale_colore))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Errore nella registrazione del PDF: {str(e)}")
        conn.rollback()
        return False
    finally:
        conn.close()