from flask import Flask
from modules.clienti import clienti_bp
from modules.fotocopiatrici import fotocopiatrici_bp
from modules.conteggi import conteggi_bp

app = Flask(__name__)
app.config.from_pyfile('instance/config.py')

# Registrazione dei Blueprint
app.register_blueprint(clienti_bp, url_prefix='/clienti')
app.register_blueprint(fotocopiatrici_bp, url_prefix='/fotocopiatrici')
app.register_blueprint(conteggi_bp, url_prefix='/conteggi')

from flask import render_template

@app.route('/')
def home():
    return render_template('dashboard.html')


if __name__ == '__main__':
    app.run(debug=True, port=5100)
