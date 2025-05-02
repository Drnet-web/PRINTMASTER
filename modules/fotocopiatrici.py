from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3
import os

fotocopiatrici_bp = Blueprint('fotocopiatrici', __name__)

DB_PATH = os.path.join(os.path.dirname(__file__), '../db/printmaster.db')

# Lista fotocopiatrici - corretto il percorso della route
@fotocopiatrici_bp.route('/', methods=['GET'])
def lista_fotocopiatrici():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Selezione fotocopiatriche e nome cliente tramite JOIN, con i campi aggiunti
    cursor.execute(''' 
        SELECT f.id, f.seriale, f.modello, f.marca, f.tipologia, f.colore, c.nome, 
               f.forfait_nero, f.forfait_colore, f.costo_copia_nero, f.costo_copia_colore
        FROM fotocopiatrici f
        LEFT JOIN clienti c ON f.cliente_id = c.id
    ''')
    fotocopiatriche = cursor.fetchall()
    print(fotocopiatriche)  # Debugging: controlla che i dati siano recuperati correttamente
    conn.close()

    return render_template('fotocopiatrici.html', fotocopiatriche=fotocopiatriche)


# Aggiungi fotocopiatrice
@fotocopiatrici_bp.route('/add', methods=['GET', 'POST'])
def add_fotocopiatrice():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome FROM clienti')
    clienti = cursor.fetchall()

    if request.method == 'POST':
        seriale = request.form['seriale'].strip()
        modello = request.form['modello'].strip()
        marca = request.form['marca'].strip()
        tipologia = request.form['tipologia'].strip()
        colore = request.form['colore'].strip()
        forfait_nero = request.form['forfait_nero'].strip()
        forfait_colore = request.form['forfait_colore'].strip()
        costo_copia_nero = request.form['costo_copia_nero'].strip()
        costo_copia_colore = request.form['costo_copia_colore'].strip()
        cliente_id = request.form['cliente_id'].strip()

        if not all([seriale, modello, marca, tipologia, colore, forfait_nero, forfait_colore, costo_copia_nero, costo_copia_colore, cliente_id]):
            conn.close()
            errore = "Tutti i campi sono obbligatori."
            return render_template('add_fotocopiatrice.html', clienti=clienti, errore=errore)

        try:
            cursor.execute('''
                INSERT INTO fotocopiatrici 
                (seriale, modello, marca, tipologia, colore, forfait_nero, forfait_colore, costo_copia_nero, costo_copia_colore, cliente_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (seriale, modello, marca, tipologia, colore, forfait_nero, forfait_colore, costo_copia_nero, costo_copia_colore, cliente_id))
            conn.commit()
            conn.close()
            return redirect(url_for('fotocopiatrici.lista_fotocopiatrici'))
        except sqlite3.IntegrityError:
            conn.close()
            errore = "Errore: seriale già presente nel sistema. Inserisci un seriale unico."
            return render_template('add_fotocopiatrice.html', clienti=clienti, errore=errore)

    conn.close()
    return render_template('add_fotocopiatrice.html', clienti=clienti, errore=None)


@fotocopiatrici_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_fotocopiatrice(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Recupero la fotocopiatrice per l'id
    cursor.execute('SELECT * FROM fotocopiatrici WHERE id = ?', (id,))
    macchina = cursor.fetchone()

    # Recupero tutti i clienti per associarli
    cursor.execute('SELECT id, nome FROM clienti')
    clienti = cursor.fetchall()

    if request.method == 'POST':
        seriale = request.form['seriale'].strip()
        modello = request.form['modello'].strip()
        marca = request.form['marca'].strip()
        tipologia = request.form['tipologia'].strip()
        colore = request.form['colore'].strip()
        forfait_nero = request.form['forfait_nero'].strip()
        forfait_colore = request.form['forfait_colore'].strip()
        costo_copia_nero = request.form['costo_copia_nero'].strip()
        costo_copia_colore = request.form['costo_copia_colore'].strip()
        cliente_id = request.form['cliente_id'].strip()

        # Se uno dei campi è vuoto, mostra un errore
        if not all([seriale, modello, marca, tipologia, colore, forfait_nero, forfait_colore, costo_copia_nero, costo_copia_colore, cliente_id]):
            conn.close()
            errore = "Tutti i campi sono obbligatori."
            return render_template('edit_fotocopiatrice.html', macchina=macchina, clienti=clienti, errore=errore)

        # Aggiorna i dati della fotocopiatrice
        try:
            cursor.execute('''
                UPDATE fotocopiatrici
                SET seriale = ?, modello = ?, marca = ?, tipologia = ?, colore = ?, forfait_nero = ?, forfait_colore = ?, costo_copia_nero = ?, costo_copia_colore = ?, cliente_id = ?
                WHERE id = ?
            ''', (seriale, modello, marca, tipologia, colore, forfait_nero, forfait_colore, costo_copia_nero, costo_copia_colore, cliente_id, id))
            conn.commit()
            conn.close()
            return redirect(url_for('fotocopiatrici.lista_fotocopiatrici'))
        except sqlite3.IntegrityError:
            conn.close()
            errore = "Errore: seriale già presente nel sistema. Inserisci un seriale unico."
            return render_template('edit_fotocopiatrice.html', macchina=macchina, clienti=clienti, errore=errore)

    conn.close()
    return render_template('edit_fotocopiatrice.html', macchina=macchina, clienti=clienti, errore=None)


@fotocopiatrici_bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_fotocopiatrice(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Recupera la fotocopiatrice
    cursor.execute('SELECT * FROM fotocopiatrici WHERE id = ?', (id,))
    macchina = cursor.fetchone()

    if not macchina:
        flash("Fotocopiatrice non trovata", "danger")
        return redirect(url_for('fotocopiatrici.lista_fotocopiatrici'))

    if request.method == 'POST':
        conferma = request.form.get('conferma')
        if conferma == 'DELETE':
            # Procedi con l'eliminazione
            cursor.execute('DELETE FROM fotocopiatrici WHERE id = ?', (id,))
            conn.commit()
            conn.close()
            flash("Fotocopiatrice eliminata con successo.", "success")
            return redirect(url_for('fotocopiatrici.lista_fotocopiatrici'))
        else:
            flash("Devi scrivere 'DELETE' per confermare l'eliminazione.", "danger")

    conn.close()
    return render_template('confirm_delete_fotocopiatrice.html', macchina=macchina)