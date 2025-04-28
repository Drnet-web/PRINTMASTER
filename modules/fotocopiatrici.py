from flask import Blueprint, render_template

fotocopiatrici_bp = Blueprint('fotocopiatrici', __name__)

@fotocopiatrici_bp.route('/')
def fotocopiatrici_home():
    return render_template('fotocopiatrici.html')
