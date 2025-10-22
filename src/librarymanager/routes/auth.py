from flask import Blueprint, request, redirect, url_for, render_template
from ..models import User
from ..extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password_hash=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # placeholder - integrate Flask-Login and password hashing
        return redirect(url_for('main.index'))
    return render_template('auth/login.html')
