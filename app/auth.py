import hashlib
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.db import get_db

auth = Blueprint('auth', __name__)


def hash_pw(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()


def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            flash('Войдите в аккаунт', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    from functools import wraps
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('user_role') not in roles:
                return render_template('403.html'), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('main.index'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, hash_pw(password))
        ).fetchone()
        if user:
            session['user_id']   = user['id']
            session['username']  = user['username']
            session['user_role'] = user['role']
            session['avatar']    = user['avatar']
            return redirect(url_for('main.index'))
        error = 'Неверный логин или пароль'
    return render_template('auth/login.html', error=error)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('main.index'))
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')
        if not username or not password:
            error = 'Заполните все поля'
        elif password != confirm:
            error = 'Пароли не совпадают'
        elif len(password) < 6:
            error = 'Пароль минимум 6 символов'
        else:
            db = get_db()
            existing = db.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()
            if existing:
                error = 'Имя пользователя занято'
            else:
                db.execute(
                    "INSERT INTO users (username, password) VALUES (?,?)",
                    (username, hash_pw(password))
                )
                db.commit()
                user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
                session['user_id']   = user['id']
                session['username']  = user['username']
                session['user_role'] = user['role']
                session['avatar']    = user['avatar']
                return redirect(url_for('main.index'))
    return render_template('auth/register.html', error=error)


@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))
