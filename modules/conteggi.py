from flask import Blueprint, render_template

conteggi_bp = Blueprint('conteggi', __name__)

@conteggi_bp.route('/')
def conteggi_home():
    return render_template('conteggi.html')
