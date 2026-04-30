from flask import Blueprint, render_template, redirect, url_for, session, abort
from app.db import get_db
from app.auth import login_required

friends_bp = Blueprint('friends', __name__, url_prefix='/friends')


def add_notification(db, user_id, text, link=None):
    db.execute("INSERT INTO notifications (user_id, text, link) VALUES (?,?,?)", (user_id, text, link))


@friends_bp.route('/')
@login_required
def index():
    db = get_db()
    uid = session['user_id']

    friends = db.execute("""
        SELECT u.id, u.username, u.avatar, u.role
        FROM friendships f
        JOIN users u ON u.id = CASE WHEN f.from_id=? THEN f.to_id ELSE f.from_id END
        WHERE (f.from_id=? OR f.to_id=?) AND f.status='accepted'
    """, (uid, uid, uid)).fetchall()

    incoming = db.execute("""
        SELECT f.id, u.id as user_id, u.username, u.avatar
        FROM friendships f
        JOIN users u ON u.id = f.from_id
        WHERE f.to_id=? AND f.status='pending'
    """, (uid,)).fetchall()

    outgoing = db.execute("""
        SELECT f.id, u.id as user_id, u.username
        FROM friendships f
        JOIN users u ON u.id = f.to_id
        WHERE f.from_id=? AND f.status='pending'
    """, (uid,)).fetchall()

    return render_template('friends/index.html',
                           friends=friends, incoming=incoming, outgoing=outgoing)


@friends_bp.route('/request/<int:to_id>', methods=['POST'])
@login_required
def send_request(to_id):
    uid = session['user_id']
    if to_id == uid:
        abort(400)
    db = get_db()
    existing = db.execute(
        "SELECT id FROM friendships WHERE (from_id=? AND to_id=?) OR (from_id=? AND to_id=?)",
        (uid, to_id, to_id, uid)
    ).fetchone()
    if not existing:
        db.execute("INSERT INTO friendships (from_id, to_id) VALUES (?,?)", (uid, to_id))
        # Уведомление получателю
        sender = session['username']
        add_notification(db, to_id,
            f'Пользователь {sender} отправил вам заявку в друзья.',
            link='/friends/')
        db.commit()
    target = db.execute("SELECT username FROM users WHERE id=?", (to_id,)).fetchone()
    return redirect(url_for('profile.view', username=target['username']))


@friends_bp.route('/accept/<int:friendship_id>', methods=['POST'])
@login_required
def accept(friendship_id):
    db = get_db()
    f = db.execute("SELECT * FROM friendships WHERE id=?", (friendship_id,)).fetchone()
    if not f or f['to_id'] != session['user_id']:
        abort(403)
    db.execute("UPDATE friendships SET status='accepted' WHERE id=?", (friendship_id,))
    # Уведомление отправителю заявки
    acceptor = session['username']
    add_notification(db, f['from_id'],
        f'Пользователь {acceptor} принял вашу заявку в друзья.',
        link=f'/profile/{acceptor}')
    db.commit()
    return redirect(url_for('friends.index'))


@friends_bp.route('/decline/<int:friendship_id>', methods=['POST'])
@login_required
def decline(friendship_id):
    db = get_db()
    f = db.execute("SELECT * FROM friendships WHERE id=?", (friendship_id,)).fetchone()
    if not f or (f['to_id'] != session['user_id'] and f['from_id'] != session['user_id']):
        abort(403)
    db.execute("DELETE FROM friendships WHERE id=?", (friendship_id,))
    db.commit()
    return redirect(url_for('friends.index'))


@friends_bp.route('/remove/<int:user_id>', methods=['POST'])
@login_required
def remove(user_id):
    uid = session['user_id']
    db = get_db()
    db.execute(
        "DELETE FROM friendships WHERE (from_id=? AND to_id=?) OR (from_id=? AND to_id=?)",
        (uid, user_id, user_id, uid)
    )
    db.commit()
    return redirect(url_for('friends.index'))
