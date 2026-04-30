from flask import Blueprint, render_template, session, jsonify, redirect, url_for
from app.db import get_db
from app.auth import login_required

notif_bp = Blueprint('notif', __name__, url_prefix='/notifications')


@notif_bp.route('/')
@login_required
def index():
    db = get_db()
    db.execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (session['user_id'],))
    db.commit()
    notifs = db.execute(
        "SELECT * FROM notifications WHERE user_id=? ORDER BY created_at DESC",
        (session['user_id'],)
    ).fetchall()
    return render_template('notifications.html', notifications=notifs)


@notif_bp.route('/delete/<int:notif_id>', methods=['POST'])
@login_required
def delete(notif_id):
    db = get_db()
    db.execute("DELETE FROM notifications WHERE id=? AND user_id=?", (notif_id, session['user_id']))
    db.commit()
    return redirect(url_for('notif.index'))


@notif_bp.route('/api/notifications/count')
def count():
    if not session.get('user_id'):
        return jsonify({'count': 0})
    db = get_db()
    row = db.execute(
        "SELECT COUNT(*) as c FROM notifications WHERE user_id=? AND is_read=0",
        (session['user_id'],)
    ).fetchone()
    return jsonify({'count': row['c']})
