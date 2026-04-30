from flask import Blueprint, request, redirect, url_for, session, abort
from app.db import get_db
from app.auth import login_required, role_required

reports_bp = Blueprint('reports', __name__, url_prefix='/report')


def add_notification(db, user_id, text, link=None):
    db.execute("INSERT INTO notifications (user_id, text, link) VALUES (?,?,?)", (user_id, text, link))


def notify_admins(db, text, link=None):
    admins = db.execute(
        "SELECT id FROM users WHERE role IN ('admin','moderator')"
    ).fetchall()
    for a in admins:
        add_notification(db, a['id'], text, link)


@reports_bp.route('/article/<int:article_id>', methods=['POST'])
@login_required
def report_article(article_id):
    reason = request.form.get('reason', '').strip()
    if not reason:
        return redirect(request.referrer or '/')
    db = get_db()
    db.execute(
        "INSERT INTO reports (reporter_id, target_type, target_id, reason) VALUES (?,?,?,?)",
        (session['user_id'], 'article', article_id, reason)
    )
    article = db.execute("SELECT title FROM articles WHERE id=?", (article_id,)).fetchone()
    title = article['title'] if article else f'#{article_id}'
    notify_admins(db, f'Новая жалоба на статью «{title}» от {session["username"]}.', link='/admin/')
    db.commit()
    return redirect(request.referrer or '/')


@reports_bp.route('/user/<int:user_id>', methods=['POST'])
@login_required
def report_user(user_id):
    reason = request.form.get('reason', '').strip()
    if not reason:
        return redirect(request.referrer or '/')
    db = get_db()
    db.execute(
        "INSERT INTO reports (reporter_id, target_type, target_id, reason) VALUES (?,?,?,?)",
        (session['user_id'], 'user', user_id, reason)
    )
    target = db.execute("SELECT username FROM users WHERE id=?", (user_id,)).fetchone()
    name = target['username'] if target else f'#{user_id}'
    notify_admins(db, f'Новая жалоба на пользователя {name} от {session["username"]}.', link='/admin/')
    db.commit()
    return redirect(request.referrer or '/')


@reports_bp.route('/resolve/<int:report_id>', methods=['POST'])
@login_required
@role_required('admin', 'moderator')
def resolve(report_id):
    db = get_db()
    r = db.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    if r:
        db.execute("UPDATE reports SET status='resolved' WHERE id=?", (report_id,))
        # Уведомить автора жалобы
        add_notification(db, r['reporter_id'],
            f'Ваша жалоба была рассмотрена и принята модератором.')
        db.commit()
    return redirect(url_for('admin.index'))


@reports_bp.route('/dismiss/<int:report_id>', methods=['POST'])
@login_required
@role_required('admin', 'moderator')
def dismiss(report_id):
    db = get_db()
    r = db.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    if r:
        db.execute("UPDATE reports SET status='dismissed' WHERE id=?", (report_id,))
        # Уведомить автора жалобы
        add_notification(db, r['reporter_id'],
            f'Ваша жалоба была рассмотрена и отклонена модератором.')
        db.commit()
    return redirect(url_for('admin.index'))
