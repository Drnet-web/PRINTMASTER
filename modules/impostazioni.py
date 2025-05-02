from flask import Blueprint, render_template, redirect, url_for, flash, send_file
import os
import datetime
import shutil
import glob

# Blueprint
impostazioni_bp = Blueprint('impostazioni', __name__, url_prefix='/impostazioni')

# Percorsi fissi
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../db/printmaster.db'))
BACKUP_FOLDER = r"C:\PRINTMASTER\backups"

@impostazioni_bp.route('/')
def pannello_impostazioni():
    backups = get_backups()
    return render_template('impostazioni.html', backups=backups)

@impostazioni_bp.route('/backup', methods=['POST'])
def crea_backup():
    # 1) Assicurati che la cartella esista
    os.makedirs(BACKUP_FOLDER, exist_ok=True)
    
    # Controlla se ci sono già 14+ backup e rimuovi i più vecchi
    paths = sorted(
        glob.glob(os.path.join(BACKUP_FOLDER, 'backup_*.db')),
        key=lambda x: os.path.basename(x),
        reverse=True
    )
    if len(paths) >= 14:
        for old in paths[13:]:  # Lascia spazio per il nuovo (quindi 13 invece di 14)
            try:
                os.remove(old)
                print(f"Backup preventivamente eliminato: {os.path.basename(old)}")
            except Exception as e:
                flash(f"Errore nell'eliminazione preventiva: {e}", 'warning')
    
    # 2) Crea il backup con nome unico e Windows-safe
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup_filename = f"backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_FOLDER, backup_filename)
    try:
        shutil.copy2(DB_PATH, backup_path)
        flash(f"Backup creato con successo: {backup_filename}", 'success')
    except Exception as e:
        flash(f"Errore nella creazione del backup: {e}", 'danger')
        return redirect(url_for('impostazioni.pannello_impostazioni'))
    
    return redirect(url_for('impostazioni.pannello_impostazioni'))

@impostazioni_bp.route('/download/<filename>')
def download_backup(filename):
    file_path = os.path.join(BACKUP_FOLDER, filename)
    if not os.path.isfile(file_path):
        flash("File di backup non trovato.", "danger")
        return redirect(url_for('impostazioni.pannello_impostazioni'))
    return send_file(file_path, as_attachment=True)

def get_backups():
    """Ritorna la lista dei backup (massimo 14, ordinati per data decrescente)."""
    if not os.path.isdir(BACKUP_FOLDER):
        return []
    paths = sorted(
        glob.glob(os.path.join(BACKUP_FOLDER, 'backup_*.db')),
        key=os.path.getmtime,
        reverse=True
    )
    backups = []
    for p in paths:
        stat = os.stat(p)
        backups.append({
            'filename': os.path.basename(p),
            'formatted_date': datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M:%S'),
            'size_mb': round(stat.st_size / (1024 * 1024), 2)
        })
    return backups

def cleanup_old_backups():
    """Mantiene solo i 14 backup più recenti."""
    paths = sorted(
        glob.glob(os.path.join(BACKUP_FOLDER, 'backup_*.db')),
        key=os.path.getmtime,
        reverse=True
    )
    # Se ci sono più di 14, elimina quelli oltre il 14° indice
    for old in paths[14:]:
        try:
            os.remove(old)
        except:
            pass
