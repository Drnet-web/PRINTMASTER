import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, '../db/printmaster.db')

SECRET_KEY = 'printmaster-secret-key'
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE}'
SQLALCHEMY_TRACK_MODIFICATIONS = False
