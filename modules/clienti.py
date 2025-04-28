from flask import Blueprint, render_template, request, redirect, url_for
import sqlite3
import os

clienti_bp = Blueprint('clienti', __name__)

# Percorso del database
DB_PATH = os.path.join(os.path.dirname(__file__), '../db/printmaster.db')

# Lista clienti
@clienti_bp.route('/', methods=['GET'])
def clienti_home():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM clienti')
    clienti = cursor.fetchall()
    conn.close()
    return render_template('clienti.html', clienti=clienti)

# Aggiungi cliente
@clienti_bp.route('/add', methods=['GET', 'POST'])
def add_cliente():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefono = request.form['telefono']
        indirizzo = request.form['indirizzo']
        citta = request.form['citta']
        provincia = request.form['provincia']
        cap = request.form['cap']

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO clienti (nome, email, telefono, indirizzo, citta, provincia, cap)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (nome, email, telefono, indirizzo, citta, provincia, cap))
        conn.commit()
        conn.close()
        return redirect(url_for('clienti.clienti_home'))
    return render_template('add_cliente.html')

# Modifica cliente
@clienti_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_cliente(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        telefono = request.form['telefono']
        indirizzo = request.form['indirizzo']
        citta = request.form['citta']
        provincia = request.form['provincia']
        cap = request.form['cap']

        cursor.execute('''
            UPDATE clienti
            SET nome = ?, email = ?, telefono = ?, indirizzo = ?, citta = ?, provincia = ?, cap = ?
            WHERE id = ?
        ''', (nome, email, telefono, indirizzo, citta, provincia, cap, id))
        conn.commit()
        conn.close()
        return redirect(url_for('clienti.clienti_home'))

    cursor.execute('SELECT * FROM clienti WHERE id = ?', (id,))
    cliente = cursor.fetchone()
    conn.close()
    return render_template('edit_cliente.html', cliente=cliente)

# Conferma eliminazione cliente
@clienti_bp.route('/delete/<int:id>', methods=['GET', 'POST'])
def delete_cliente(id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Prima di eliminare, controllo se il cliente ha fotocopiatrici
    cursor.execute('SELECT COUNT(*) FROM fotocopiatrici WHERE cliente_id = ?', (id,))
    fotocopiatrici_count = cursor.fetchone()[0]

    if request.method == 'POST':
        conferma = request.form['conferma']

        if fotocopiatrici_count > 0:
            conn.close()
            errore = "Impossibile eliminare: il cliente ha fotocopiatrici assegnate."
            return render_template('confirm_delete_cliente.html', id=id, errore=errore)

        if conferma.strip().upper() == "DELETE":
            cursor.execute('DELETE FROM clienti WHERE id = ?', (id,))
            conn.commit()
            conn.close()
            return redirect(url_for('clienti.clienti_home'))
        else:
            errore = "Scritta di conferma errata. Devi scrivere esattamente 'DELETE'."
            conn.close()
            return render_template('confirm_delete_cliente.html', id=id, errore=errore)

    conn.close()
    return render_template('confirm_delete_cliente.html', id=id, errore=None)

