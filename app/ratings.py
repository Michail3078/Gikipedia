from flask import Blueprint, request, jsonify, session
from app.db import get_db
from app.auth import login_required

ratings = Blueprint('ratings', __name__)

@ratings.route('/api/article/<int:article_id>/rate', methods=['POST'])
@login_required
def rate_article(article_id):
    """Поставить оценку статье (1-5)"""
    rating = request.form.get('rating', type=int)
    
    if not rating or rating < 1 or rating > 5:
        return jsonify({'error': 'Оценка должна быть от 1 до 5'}), 400
    
    db = get_db()
    
    # Проверяем существование статьи
    article = db.execute("SELECT id FROM articles WHERE id=?", (article_id,)).fetchone()
    if not article:
        return jsonify({'error': 'Статья не найдена'}), 404
    
    # Проверяем, не оценивал ли уже пользователь
    existing = db.execute(
        "SELECT id, rating FROM article_ratings WHERE article_id=? AND user_id=?",
        (article_id, session['user_id'])
    ).fetchone()
    
    if existing:
        # Обновляем существующую оценку
        db.execute(
            "UPDATE article_ratings SET rating=? WHERE id=?",
            (rating, existing['id'])
        )
        # Обновляем общий рейтинг статьи
        db.execute("""
            UPDATE articles SET rating=(
                SELECT AVG(rating) FROM article_ratings WHERE article_id=?
            ) WHERE id=?
        """, (article_id, article_id))
    else:
        # Добавляем новую оценку
        db.execute(
            "INSERT INTO article_ratings (article_id, user_id, rating) VALUES (?,?,?)",
            (article_id, session['user_id'], rating)
        )
        # Обновляем общий рейтинг статьи
        db.execute("""
            UPDATE articles SET rating=(
                SELECT AVG(rating) FROM article_ratings WHERE article_id=?
            ) WHERE id=?
        """, (article_id, article_id))
    
    db.commit()
    
    # Получаем обновленный рейтинг
    article = db.execute("SELECT rating FROM articles WHERE id=?", (article_id,)).fetchone()
    user_rating = db.execute(
        "SELECT rating FROM article_ratings WHERE article_id=? AND user_id=?",
        (article_id, session['user_id'])
    ).fetchone()
    
    return jsonify({
        'success': True,
        'article_rating': float(article['rating']) if article['rating'] else 0,
        'user_rating': user_rating['rating'] if user_rating else None
    })

@ratings.route('/api/article/<int:article_id>/rating')
def get_article_rating(article_id):
    """Получить информацию об оценках статьи"""
    db = get_db()
    
    article = db.execute("SELECT rating FROM articles WHERE id=?", (article_id,)).fetchone()
    if not article:
        return jsonify({'error': 'Статья не найдена'}), 404
    
    # Получаем количество оценок
    count_result = db.execute(
        "SELECT COUNT(*) as count FROM article_ratings WHERE article_id=?",
        (article_id,)
    ).fetchone()
    
    # Получаем оценку текущего пользователя (если авторизован)
    user_rating = None
    if session.get('user_id'):
        user_rating = db.execute(
            "SELECT rating FROM article_ratings WHERE article_id=? AND user_id=?",
            (article_id, session['user_id'])
        ).fetchone()
    
    return jsonify({
        'article_rating': float(article['rating']) if article['rating'] else 0,
        'rating_count': count_result['count'] if count_result else 0,
        'user_rating': user_rating['rating'] if user_rating else None
    })