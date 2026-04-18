import os
from flask import Flask, render_template, redirect, url_for, flash, request, session
from flask_login import LoginManager
from models import db, User
from routes.auth import auth_bp
from routes.worker import worker_bp
from routes.employer import employer_bp
from routes.admin import admin_bp
from routes.verify import verify_bp
from werkzeug.middleware.proxy_fix import ProxyFix
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Professional config with environment variables
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'pramaan-shadow-key-sdg8-2024')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pramaan.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_SECURE', 'False').lower() == 'true'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 604800  # 7 days
    
    # Production security
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)

    login_manager = LoginManager(app)
    login_manager.login_view = 'auth.worker_login'
    login_manager.login_message = '🔐 Please log in to continue.'
    login_manager.login_message_category = 'warning'
    login_manager.session_protection = 'strong'

    @login_manager.user_loader
    def load_user(uid):
        try:
            return User.query.get(int(uid))
        except:
            return None

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(worker_bp)
    app.register_blueprint(employer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(verify_bp)

    # Landing page
    @app.route('/')
    def index():
        return render_template('index.html')

    # Professional error handlers
    @app.errorhandler(404)
    def not_found(e):
        if request.path.startswith('/api/'):
            return {'error': 'Not found'}, 404
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        logger.error(f"Server Error: {str(e)}")
        db.session.rollback()
        if request.path.startswith('/api/'):
            return {'error': 'Internal server error'}, 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(e):
        if request.path.startswith('/api/'):
            return {'error': 'Forbidden'}, 403
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))

    # Jinja helpers
    @app.template_filter('score_class')
    def score_class(score):
        if score >= 80: return 'badge-high'
        if score >= 60: return 'badge-mid'
        return 'badge-low'
    
    @app.template_filter('format_date')
    def format_date(date):
        if date:
            return date.strftime('%b %d, %Y')
        return ''
    
    @app.template_filter('time_ago')
    def time_ago(date):
        from datetime import datetime
        if not date:
            return ''
        diff = datetime.utcnow() - date
        if diff.days > 30:
            return date.strftime('%b %d')
        elif diff.days > 0:
            return f"{diff.days}d ago"
        elif diff.seconds > 3600:
            return f"{diff.seconds // 3600}h ago"
        elif diff.seconds > 60:
            return f"{diff.seconds // 60}m ago"
        return "just now"

    # Context processor for global variables
    @app.context_processor
    def utility_processor():
        from datetime import datetime
        return dict(current_year=datetime.utcnow().year)

    # Initialize database
    with app.app_context():
        db.create_all()
        from routes.seed_data import seed_all
        seed_all(app)
        logger.info("Application initialized successfully")

    return app


app = create_app()

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 PRAMAAN SHADOW - Ready")
    print("="*60)
    print("📍 URL: http://localhost:5000")
    print("🔐 Demo Logins:")
    print("   Worker:   worker@demo.com / worker123")
    print("   Employer: hr@techcorp.io / Employer@123")
    print("   Admin:    admin@pramaan.io / Admin@123")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)