import re
from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from app.db import get_db
from app.auth import login_required, role_required

articles = Blueprint('articles', __name__, url_prefix='/wiki')


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text


@articles.route('/')
def list_articles():
    db = get_db()
    arts = db.execute(
        "SELECT a.*, u.username FROM articles a JOIN users u ON a.author_id=u.id ORDER BY a.created_at DESC"
    ).fetchall()
    return render_template('articles/list.html', articles=arts)


@articles.route('/<slug>')
def view(slug):
    db = get_db()
    article = db.execute(
        "SELECT a.*, u.username FROM articles a JOIN users u ON a.author_id=u.id WHERE a.slug=?",
        (slug,)
    ).fetchone()
    if not article:
        abort(404)
    return render_template('articles/view.html', article=article)


@articles.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    error = None
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        body  = request.form.get('body', '').strip()
        if not title or not body:
            error = 'Заполните все поля'
        else:
            slug = slugify(title)
            db = get_db()
            existing = db.execute("SELECT id FROM articles WHERE slug=?", (slug,)).fetchone()
            if existing:
                error = 'Статья с таким названием уже существует'
            else:
                db.execute(
                    "INSERT INTO articles (slug, title, body, author_id) VALUES (?,?,?,?)",
                    (slug, title, body, session['user_id'])
                )
                db.commit()
                return redirect(url_for('articles.view', slug=slug))
    return render_template('articles/edit.html', article=None, error=error)


@articles.route('/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit(slug):
    db = get_db()
    article = db.execute("SELECT * FROM articles WHERE slug=?", (slug,)).fetchone()
    if not article:
        abort(404)

    # Только автор, модератор или админ могут редактировать
    role = session.get('user_role')
    if article['author_id'] != session['user_id'] and role not in ('moderator', 'admin'):
        abort(403)

    error = None
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        body  = request.form.get('body', '').strip()
        if not title or not body:
            error = 'Заполните все поля'
        else:
            db.execute(
                "UPDATE articles SET title=?, body=?, updated_at=CURRENT_TIMESTAMP WHERE slug=?",
                (title, body, slug)
            )
            db.commit()
            return redirect(url_for('articles.view', slug=slug))
    return render_template('articles/edit.html', article=article, error=error)


@articles.route('/<slug>/delete', methods=['POST'])
@login_required
def delete(slug):
    db = get_db()
    article = db.execute("SELECT * FROM articles WHERE slug=?", (slug,)).fetchone()
    if not article:
        abort(404)
    role = session.get('user_role')
    if article['author_id'] != session['user_id'] and role not in ('moderator', 'admin'):
        abort(403)
    db.execute("DELETE FROM articles WHERE slug=?", (slug,))
    db.commit()
    return redirect(url_for('articles.list_articles'))
