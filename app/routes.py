from flask import Blueprint, render_template, request, session, jsonify
from app.db import get_db

main = Blueprint('main', __name__)


@main.route('/')
def index():
    db = get_db()
    recent = db.execute(
        "SELECT a.*, u.username FROM articles a JOIN users u ON a.author_id=u.id ORDER BY a.created_at DESC LIMIT 6"
    ).fetchall()
    return render_template('index.html', recent=recent)


@main.route('/search')
def search():
    q = request.args.get('q', '').strip()
    articles = []
    users = []
    if q:
        db = get_db()
        # Ищем по названию, содержанию и тегам
        articles = db.execute(
            "SELECT * FROM articles WHERE title LIKE ? OR body LIKE ? OR tag LIKE ? ORDER BY rating DESC",
            (f'%{q}%', f'%{q}%', f'%{q}%')
        ).fetchall()
        users = db.execute(
            "SELECT id, username, role, bio FROM users WHERE username LIKE ?",
            (f'%{q}%',)
        ).fetchall()
    return render_template('search.html', q=q, results=articles, users=users)


@main.route('/api/top-rated')
def top_rated():
    """API для получения самых популярных статей"""
    db = get_db()
    # Берем 10 статей с самым высоким рейтингом
    articles = db.execute("""
        SELECT a.*, u.username 
        FROM articles a 
        JOIN users u ON a.author_id = u.id 
        WHERE a.rating > 0 
        ORDER BY a.rating DESC, a.created_at DESC 
        LIMIT 10
    """).fetchall()
    
    result = []
    for article in articles:
        result.append({
            'id': article['id'],
            'slug': article['slug'],
            'title': article['title'],
            'rating': float(article['rating']) if article['rating'] else 0,
            'username': article['username']
        })
    
    return jsonify(result)