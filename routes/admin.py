from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, Skill, Question, User, VerifiedSkill, Shortlist, Message, TestAttempt

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = {
        'workers': User.query.filter_by(role='worker').count(),
        'employers': User.query.filter_by(role='employer').count(),
        'skills': Skill.query.count(),
        'questions': Question.query.count(),
        'verified': VerifiedSkill.query.count(),
        'shortlists': Shortlist.query.count(),
        'messages': Message.query.count(),
        'attempts': TestAttempt.query.count(),
    }
    recent_workers = User.query.filter_by(role='worker').order_by(User.created_at.desc()).limit(8).all()
    top_workers = User.query.filter_by(role='worker').order_by(User.shadow_score.desc()).limit(5).all()
    recent_verified = VerifiedSkill.query.order_by(VerifiedSkill.verified_at.desc()).limit(6).all()
    return render_template('admin_dashboard.html', stats=stats, recent_workers=recent_workers,
                          top_workers=top_workers, recent_verified=recent_verified)

@admin_bp.route('/skills', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_skills():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        category = request.form.get('category', '').strip()
        icon = request.form.get('icon', 'fa-code').strip()
        if not name or not category:
            flash('Skill name and category are required.', 'danger')
        elif Skill.query.filter_by(name=name).first():
            flash('A skill with that name already exists.', 'danger')
        else:
            db.session.add(Skill(name=name, category=category, icon=icon))
            db.session.commit()
            flash(f'Skill "{name}" added.', 'success')
        return redirect(url_for('admin.manage_skills'))
    
    skills = Skill.query.order_by(Skill.category, Skill.name).all()
    skill_stats = {}
    for s in skills:
        skill_stats[s.id] = {
            'q_count': Question.query.filter_by(skill_id=s.id).count(),
            'verified': VerifiedSkill.query.filter_by(skill_id=s.id).count(),
        }
    return render_template('admin_skills.html', skills=skills, skill_stats=skill_stats)

@admin_bp.route('/skills/delete/<int:sid>', methods=['POST'])
@login_required
@admin_required
def delete_skill(sid):
    skill = Skill.query.get_or_404(sid)
    name = skill.name
    db.session.delete(skill)
    db.session.commit()
    flash(f'Skill "{name}" deleted.', 'info')
    return redirect(url_for('admin.manage_skills'))

@admin_bp.route('/questions', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_questions():
    skills = Skill.query.order_by(Skill.category, Skill.name).all()
    selected_sid = request.args.get('skill_id', type=int)
    
    if request.method == 'POST':
        sid = request.form.get('skill_id', type=int)
        qtext = request.form.get('question_text', '').strip()
        oa, ob, oc, od = request.form.get('option_a', '').strip(), request.form.get('option_b', '').strip(), request.form.get('option_c', '').strip(), request.form.get('option_d', '').strip()
        ans = request.form.get('correct_answer', '').upper()
        
        if not all([sid, qtext, oa, ob, oc, od]) or ans not in ('A','B','C','D'):
            flash('All fields are required and correct answer must be A-D.', 'danger')
        else:
            db.session.add(Question(skill_id=sid, question_text=qtext, option_a=oa, option_b=ob, option_c=oc, option_d=od, correct_answer=ans))
            db.session.commit()
            flash('Question added.', 'success')
            selected_sid = sid
        return redirect(url_for('admin.manage_questions', skill_id=selected_sid))
    
    questions = Question.query.filter_by(skill_id=selected_sid).all() if selected_sid else []
    return render_template('admin_questions.html', skills=skills, questions=questions, selected_sid=selected_sid)

@admin_bp.route('/questions/delete/<int:qid>', methods=['POST'])
@login_required
@admin_required
def delete_question(qid):
    q = Question.query.get_or_404(qid)
    sid = q.skill_id
    db.session.delete(q)
    db.session.commit()
    flash('Question deleted.', 'info')
    return redirect(url_for('admin.manage_questions', skill_id=sid))

@admin_bp.route('/questions/edit/<int:qid>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_question(qid):
    q = Question.query.get_or_404(qid)
    if request.method == 'POST':
        q.question_text = request.form.get('question_text', '').strip()
        q.option_a = request.form.get('option_a', '').strip()
        q.option_b = request.form.get('option_b', '').strip()
        q.option_c = request.form.get('option_c', '').strip()
        q.option_d = request.form.get('option_d', '').strip()
        q.correct_answer = request.form.get('correct_answer', '').upper()
        db.session.commit()
        flash('Question updated successfully.', 'success')
        return redirect(url_for('admin.manage_questions', skill_id=q.skill_id))
    return render_template('admin_edit_question.html', q=q)

@admin_bp.route('/users')
@login_required
@admin_required
def manage_users():
    role = request.args.get('role', 'worker')
    search = request.args.get('search', '').strip()
    query = User.query.filter_by(role=role)
    if search:
        query = query.filter(db.or_(User.name.ilike(f'%{search}%'), User.email.ilike(f'%{search}%'), User.anonymous_id.ilike(f'%{search}%')))
    users = query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users, role=role, search=search)

@admin_bp.route('/users/delete/<int:uid>', methods=['POST'])
@login_required
@admin_required
def delete_user(uid):
    user = User.query.get_or_404(uid)
    if user.role == 'admin':
        flash('Cannot delete admin accounts.', 'danger')
        return redirect(url_for('admin.manage_users'))
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{user.name}" deleted.', 'info')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/verified-skills')
@login_required
@admin_required
def verified_skills():
    page = request.args.get('page', 1, type=int)
    records = VerifiedSkill.query.order_by(VerifiedSkill.verified_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin_verified.html', records=records)

@admin_bp.route('/shortlists')
@login_required
@admin_required
def view_shortlists():
    shortlists = Shortlist.query.order_by(Shortlist.created_at.desc()).all()
    data = []
    for sl in shortlists:
        data.append({'sl': sl, 'employer': User.query.get(sl.employer_id), 'worker': User.query.get(sl.worker_id)})
    return render_template('admin_shortlists.html', data=data)