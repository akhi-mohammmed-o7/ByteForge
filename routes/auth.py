from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from utils.hash_generator import generate_anonymous_id
import re

auth_bp = Blueprint('auth', __name__)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, ""

def _unique_anon_id():
    aid = generate_anonymous_id()
    while User.query.filter_by(anonymous_id=aid).first():
        aid = generate_anonymous_id()
    return aid

# ── WORKER ──────────────────────────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def worker_register():
    if current_user.is_authenticated:
        return redirect(url_for('worker.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        pw = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        
        # Validation
        if not all([name, email, pw, confirm]):
            flash('All fields are required.', 'danger')
        elif len(name) < 3:
            flash('Name must be at least 3 characters.', 'danger')
        elif not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
        elif pw != confirm:
            flash('Passwords do not match.', 'danger')
        else:
            valid, msg = validate_password(pw)
            if not valid:
                flash(msg, 'danger')
            elif User.query.filter_by(email=email).first():
                flash('Email already registered. Please login instead.', 'danger')
            else:
                user = User(
                    name=name,
                    email=email,
                    password_hash=generate_password_hash(pw),
                    role='worker',
                    anonymous_id=_unique_anon_id()
                )
                db.session.add(user)
                db.session.commit()
                flash('✅ Registration successful! Welcome to PRAMAAN SHADOW.', 'success')
                return redirect(url_for('auth.worker_login'))
    
    return render_template('worker_register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def worker_login():
    if current_user.is_authenticated:
        if current_user.role == 'worker':
            return redirect(url_for('worker.dashboard'))
        elif current_user.role == 'employer':
            return redirect(url_for('employer.dashboard'))
        elif current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        pw = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email, role='worker').first()
        if user and check_password_hash(user.password_hash, pw):
            login_user(user, remember=bool(remember))
            flash(f'Welcome back, {user.anonymous_id}!', 'success')
            nxt = request.args.get('next')
            if nxt and nxt.startswith('/'):
                return redirect(nxt)
            return redirect(url_for('worker.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('worker_login.html')


# ── EMPLOYER ─────────────────────────────────────────────────────────────────
@auth_bp.route('/employer/login', methods=['GET', 'POST'])
def employer_login():
    if current_user.is_authenticated and current_user.role == 'employer':
        return redirect(url_for('employer.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        pw = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email, role='employer').first()
        if user and check_password_hash(user.password_hash, pw):
            login_user(user, remember=bool(remember))
            flash(f'Welcome, {user.name}!', 'success')
            return redirect(url_for('employer.dashboard'))
        else:
            flash('Invalid employer credentials.', 'danger')
    
    return render_template('employer_login.html')


@auth_bp.route('/employer/register', methods=['GET', 'POST'])
def employer_register():
    if current_user.is_authenticated:
        return redirect(url_for('employer.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        pw = request.form.get('password', '')
        company = request.form.get('company', '').strip()
        
        if not all([name, email, pw]):
            flash('All fields are required.', 'danger')
        elif not validate_email(email):
            flash('Please enter a valid email address.', 'danger')
        elif len(pw) < 8:
            flash('Password must be at least 8 characters.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
        else:
            # Add company to name if provided
            full_name = f"{name} ({company})" if company else name
            user = User(
                name=full_name,
                email=email,
                password_hash=generate_password_hash(pw),
                role='employer'
            )
            db.session.add(user)
            db.session.commit()
            flash('✅ Employer account created! Please log in.', 'success')
            return redirect(url_for('auth.employer_login'))
    
    return render_template('employer_register.html')


# ── ADMIN ─────────────────────────────────────────────────────────────────────
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.role == 'admin':
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        pw = request.form.get('password', '')
        
        user = User.query.filter_by(email=email, role='admin').first()
        if user and check_password_hash(user.password_hash, pw):
            login_user(user, remember=True)
            flash('Admin access granted.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')
    
    return render_template('admin_login.html')


# ── LOGOUT ────────────────────────────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    role = current_user.role
    name = current_user.anonymous_id if role == 'worker' else current_user.name
    logout_user()
    flash(f'Goodbye, {name}! You have been logged out.', 'info')
    
    if role == 'employer':
        return redirect(url_for('auth.employer_login'))
    if role == 'admin':
        return redirect(url_for('auth.admin_login'))
    return redirect(url_for('auth.worker_login'))