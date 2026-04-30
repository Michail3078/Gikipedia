from flask import Flask, session
from app.db import close_db, init_db


def create_app():
    app = Flask(__name__)
    app.secret_key = 'dev-secret-key-change-in-prod'

    # Init DB on first run
    init_db()

    # Teardown
    app.teardown_appcontext(close_db)

    # Blueprints
    from app.routes        import main
    from app.auth          import auth
    from app.articles      import articles
    from app.profile       import profile
    from app.admin         import admin_bp
    from app.notifications import notif_bp
    from app.chat          import chat_bp
    from app.friends       import friends_bp
    from app.reports       import reports_bp

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(articles)
    app.register_blueprint(profile)
    app.register_blueprint(admin_bp)
    app.register_blueprint(notif_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(friends_bp)
    app.register_blueprint(reports_bp)

    # API: notification count (used by JS)
    from app.notifications import count as notif_count
    app.add_url_rule('/api/notifications/count', 'api_notif_count', notif_count)

    # Inject current user into all templates
    @app.context_processor
    def inject_user():
        user = None
        if session.get('user_id'):
            from app.db import get_db
            user = get_db().execute(
                "SELECT * FROM users WHERE id=?", (session['user_id'],)
            ).fetchone()
        return dict(current_user=user)

    # Custom Jinja filters
    import markupsafe
    @app.template_filter('nl2br')
    def nl2br(value):
        escaped = markupsafe.escape(value)
        return markupsafe.Markup(str(escaped).replace('\n', '<br>\n'))

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return __import__('flask').render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return __import__('flask').render_template('403.html'), 403

    return app
