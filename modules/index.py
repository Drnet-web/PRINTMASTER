from flask import Blueprint, render_template
import sqlite3
import os

home_bp = Blueprint('home', __name__)
DB_PATH = os.path.join(os.path.dirname(__file__), '../db/printmaster.db')

@home_bp.route('/')
def dashboard():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM clienti')
    total_clienti = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM fotocopiatrici')
    total_fotocopiatrici = cursor.fetchone()[0]

    cursor.execute('SELECT tipologia, COUNT(*) FROM fotocopiatrici GROUP BY tipologia')
    fotocopiatrici_per_tipologia = cursor.fetchall()

    conn.close()
    return render_template('index.html',
                           total_clienti=total_clienti,
                           total_fotocopiatrici=total_fotocopiatrici,
                           fotocopiatrici_per_tipologia=fotocopiatrici_per_tipologia)
