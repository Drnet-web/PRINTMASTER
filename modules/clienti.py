from flask import Blueprint, render_template

clienti_bp = Blueprint('clienti', __name__)

@clienti_bp.route('/')
def clienti_home():
    return render_template('clienti.html')
