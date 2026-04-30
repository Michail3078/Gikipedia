from flask import Blueprint, render_template, request, redirect, url_for, session
from app.db import get_db
from app.auth import login_required, role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@login_required
@role_required('admin', 'moderator')
def index():
    db = get_db()
    users    = db.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    arts     = db.execute(
        "SELECT a.*, u.username FROM articles a JOIN users u ON a.author_id=u.id ORDER BY a.created_at DESC"
    ).fetchall()

    # Жалобы на статьи
    article_reports = db.execute("""
        SELECT r.*, u.username as reporter_name, a.title as target_name, a.slug as target_slug
        FROM reports r
        JOIN users u ON r.reporter_id = u.id
        JOIN articles a ON r.target_id = a.id
        WHERE r.target_type='article' AND r.status='open'
        ORDER BY r.created_at DESC
    """).fetchall()

    # Жалобы на пользователей
    user_reports = db.execute("""
        SELECT r.*, u.username as reporter_name, t.username as target_name
        FROM reports r
        JOIN users u ON r.reporter_id = u.id
        JOIN users t ON r.target_id = t.id
        WHERE r.target_type='user' AND r.status='open'
        ORDER BY r.created_at DESC
    """).fetchall()

    return render_template('admin/index.html',
                           users=users, articles=arts,
                           article_reports=article_reports,
                           user_reports=user_reports)


@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@login_required
@role_required('admin')
def change_role(user_id):
    new_role = request.form.get('role')
    if new_role in ('user', 'moderator', 'admin'):
        db = get_db()
        db.execute("UPDATE users SET role=? WHERE id=?", (new_role, user_id))
        db.commit()
    return redirect(url_for('admin.index'))


@admin_bp.route('/articles/<int:article_id>/delete', methods=['POST'])
@login_required
@role_required('admin', 'moderator')
def delete_article(article_id):
    db = get_db()
    db.execute("DELETE FROM articles WHERE id=?", (article_id,))
    db.commit()
    return redirect(url_for('admin.index'))
