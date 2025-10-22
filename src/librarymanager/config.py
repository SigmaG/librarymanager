import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.join(basedir, '..', '..', 'instance')), 'library.sqlite3')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # pagination default
    ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', '10'))
