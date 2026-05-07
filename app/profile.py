from flask import Blueprint, render_template, request, redirect, url_for, session, abort
from app.db import get_db
from app.auth import login_required

profile = Blueprint('profile', __name__, url_prefix='/profile')


@profile.route('/<username>')
def view(username):
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    if not user:
        abort(404)

    user_articles = db.execute(
        "SELECT * FROM articles WHERE author_id=? ORDER BY created_at DESC",
        (user['id'],)
    ).fetchall()

    friendship = None
    if session.get('user_id') and session['user_id'] != user['id']:
        friendship = db.execute("""
            SELECT * FROM friendships
            WHERE (from_id=? AND to_id=?) OR (from_id=? AND to_id=?)
        """, (session['user_id'], user['id'], user['id'], session['user_id'])).fetchone()

    return render_template('profile/view.html',
                           profile_user=user,
                           articles=user_articles,
                           friendship=friendship)


@profile.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id=?", (session['user_id'],)).fetchone()
    error = None
    success = None
    if request.method == 'POST':
        bio = request.form.get('bio', '').strip()
        avatar = request.form.get('avatar', '').strip()
        db.execute(
            "UPDATE users SET bio=?, avatar=? WHERE id=?",
            (bio, avatar or None, session['user_id'])
        )
        db.commit()
        success = 'Профиль обновлён'
    return render_template('profile/settings.html', user=user, error=error, success=success)
