from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, VerifiedSkill, Shortlist, Skill, Message

employer_bp = Blueprint('employer', __name__, url_prefix='/employer')

def employer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'employer':
            flash('Employer access required.', 'danger')
            return redirect(url_for('auth.employer_login'))
        return f(*args, **kwargs)
    return decorated

@employer_bp.route('/dashboard')
@login_required
@employer_required
def dashboard():
    shortlists = Shortlist.query.filter_by(employer_id=current_user.id).order_by(Shortlist.created_at.desc()).all()
    sl_data = []
    for sl in shortlists:
        worker = User.query.get(sl.worker_id)
        if worker:
            skills = VerifiedSkill.query.filter_by(user_id=worker.id).order_by(VerifiedSkill.score.desc()).all()
            sl_data.append({'shortlist': sl, 'worker': worker, 'skills': skills})
    unread = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    return render_template('employer_dashboard.html', sl_data=sl_data, unread=unread)

@employer_bp.route('/merit-board')
@login_required
@employer_required
def merit_board():
    skill_id = request.args.get('skill_id', type=int)
    min_score = request.args.get('min_score', 0, type=float)
    sort_by = request.args.get('sort', 'shadow')
    
    all_skills = Skill.query.order_by(Skill.category, Skill.name).all()
    sl_worker_ids = {sl.worker_id for sl in Shortlist.query.filter_by(employer_id=current_user.id).all()}
    
    if skill_id:
        vs_rows = VerifiedSkill.query.filter(VerifiedSkill.skill_id == skill_id, VerifiedSkill.score >= min_score).all()
        worker_ids = {vs.user_id for vs in vs_rows}
    else:
        vs_rows = VerifiedSkill.query.filter(VerifiedSkill.score >= min_score).all()
        worker_ids = {vs.user_id for vs in vs_rows}
    
    candidates = []
    seen = set()
    for wid in worker_ids:
        if wid in seen: continue
        seen.add(wid)
        worker = User.query.get(wid)
        if not worker or worker.role != 'worker': continue
        skills = VerifiedSkill.query.filter_by(user_id=wid).order_by(VerifiedSkill.score.desc()).all()
        candidates.append({'worker_id': wid, 'anonymous_id': worker.anonymous_id, 
                          'shadow_score': worker.shadow_score, 'trust_score': worker.trust_score,
                          'skill_count': len(skills), 'skills': skills, 'is_shortlisted': wid in sl_worker_ids})
    
    if sort_by == 'trust':
        candidates.sort(key=lambda c: c['trust_score'], reverse=True)
    elif sort_by == 'skills':
        candidates.sort(key=lambda c: c['skill_count'], reverse=True)
    else:
        candidates.sort(key=lambda c: c['shadow_score'], reverse=True)
    
    return render_template('employer_merit_board.html', candidates=candidates, all_skills=all_skills,
                          selected_skill=skill_id, min_score=min_score, sort_by=sort_by, total=len(candidates))

@employer_bp.route('/shortlist/<int:worker_id>', methods=['POST'])
@login_required
@employer_required
def shortlist(worker_id):
    worker = User.query.filter_by(id=worker_id, role='worker').first_or_404()
    existing = Shortlist.query.filter_by(employer_id=current_user.id, worker_id=worker_id).first()
    if existing:
        flash(f'{worker.anonymous_id} is already in your shortlist.', 'info')
    else:
        note = request.form.get('note', '')
        db.session.add(Shortlist(employer_id=current_user.id, worker_id=worker_id, note=note))
        db.session.commit()
        flash(f'✓ {worker.anonymous_id} shortlisted!', 'success')
    return redirect(request.referrer or url_for('employer.merit_board'))

@employer_bp.route('/remove-shortlist/<int:worker_id>', methods=['POST'])
@login_required
@employer_required
def remove_shortlist(worker_id):
    sl = Shortlist.query.filter_by(employer_id=current_user.id, worker_id=worker_id).first()
    if sl:
        db.session.delete(sl)
        db.session.commit()
        flash('Candidate removed from shortlist.', 'info')
    return redirect(request.referrer or url_for('employer.dashboard'))

@employer_bp.route('/reveal/<int:worker_id>', methods=['POST'])
@login_required
@employer_required
def reveal_identity(worker_id):
    sl = Shortlist.query.filter_by(employer_id=current_user.id, worker_id=worker_id).first()
    if not sl:
        flash('You must shortlist this candidate first.', 'warning')
        return redirect(url_for('employer.merit_board'))
    sl.revealed = True
    db.session.commit()
    flash('Identity revealed. Handle this information responsibly.', 'success')
    return redirect(url_for('employer.dashboard'))

@employer_bp.route('/message/<int:worker_id>', methods=['GET', 'POST'])
@login_required
@employer_required
def send_message(worker_id):
    sl = Shortlist.query.filter_by(employer_id=current_user.id, worker_id=worker_id, revealed=True).first()
    if not sl:
        flash('You can only message candidates you have shortlisted and revealed.', 'warning')
        return redirect(url_for('employer.dashboard'))
    worker = User.query.get_or_404(worker_id)
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        body = request.form.get('body', '').strip()
        if not subject or not body:
            flash('Subject and message body are required.', 'danger')
        else:
            db.session.add(Message(sender_id=current_user.id, receiver_id=worker_id, subject=subject, body=body))
            db.session.commit()
            flash(f'Message sent to {worker.anonymous_id}!', 'success')
            return redirect(url_for('employer.dashboard'))
    return render_template('employer_message.html', worker=worker, sl=sl)

@employer_bp.route('/inbox')
@login_required
@employer_required
def inbox():
    messages = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.sent_at.desc()).all()
    for m in messages:
        m.is_read = True
    db.session.commit()
    return render_template('employer_inbox.html', messages=messages)