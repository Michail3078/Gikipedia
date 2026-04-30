from flask import Blueprint, render_template, request, redirect, url_for, session
from app.db import get_db
from app.auth import login_required

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')


@chat_bp.route('/')
@login_required
def index():
    db = get_db()
    # Список диалогов (уникальные собеседники)
    contacts = db.execute("""
        SELECT DISTINCT u.id, u.username, u.avatar
        FROM messages m
        JOIN users u ON (u.id = CASE WHEN m.from_id=? THEN m.to_id ELSE m.from_id END)
        WHERE m.from_id=? OR m.to_id=?
    """, (session['user_id'], session['user_id'], session['user_id'])).fetchall()
    return render_template('chat/index.html', contacts=contacts)


@chat_bp.route('/<int:user_id>', methods=['GET', 'POST'])
@login_required
def dialog(user_id):
    db = get_db()
    other = db.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    if not other:
        return redirect(url_for('chat.index'))

    if request.method == 'POST':
        text = request.form.get('text', '').strip()
        if text:
            db.execute(
                "INSERT INTO messages (from_id, to_id, text) VALUES (?,?,?)",
                (session['user_id'], user_id, text)
            )
            db.commit()
        return redirect(url_for('chat.dialog', user_id=user_id))

    msgs = db.execute("""
        SELECT m.*, u.username as sender_name
        FROM messages m JOIN users u ON m.from_id=u.id
        WHERE (m.from_id=? AND m.to_id=?) OR (m.from_id=? AND m.to_id=?)
        ORDER BY m.created_at ASC
    """, (session['user_id'], user_id, user_id, session['user_id'])).fetchall()
    return render_template('chat/dialog.html', other=other, messages=msgs)
