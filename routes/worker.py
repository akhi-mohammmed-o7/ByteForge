import io, base64, random
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required, current_user
from models import db, Skill, VerifiedSkill, Question, User, TestAttempt, Message
from utils.hash_generator import generate_skill_hash
import qrcode

worker_bp = Blueprint('worker', __name__, url_prefix='/worker')


def worker_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'worker':
            flash('Worker access required.', 'danger')
            return redirect(url_for('auth.worker_login'))
        return f(*args, **kwargs)
    return decorated


def _recalc_scores(user):
    """Recalculate shadow_score and trust_score from all verified skills."""
    all_vs = VerifiedSkill.query.filter_by(user_id=user.id).all()
    if all_vs:
        user.shadow_score = round(sum(v.score for v in all_vs) / len(all_vs), 2)
        user.trust_score = min(1000.0, round(sum(v.score * 3 for v in all_vs), 1))
    else:
        user.shadow_score = 0.0
        user.trust_score = 0.0


def _make_qr(data: str) -> str:
    """Return base64 PNG QR code."""
    qr = qrcode.QRCode(version=1, box_size=6, border=2,
                       error_correction=qrcode.constants.ERROR_CORRECT_L)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#00f2ff", back_color="#0b0e14")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()


# ── DASHBOARD ─────────────────────────────────────────────────────────────────
@worker_bp.route('/dashboard')
@login_required
@worker_required
def dashboard():
    verified = VerifiedSkill.query.filter_by(user_id=current_user.id)\
                    .order_by(VerifiedSkill.verified_at.desc()).all()
    verified_skills = []
    for v in verified:
        skill = Skill.query.get(v.skill_id)
        if skill:
            verified_skills.append({'name': skill.name, 'score': v.score})
    
    attempts = TestAttempt.query.filter_by(user_id=current_user.id)\
                    .order_by(TestAttempt.taken_at.desc()).limit(5).all()
    inbox_count = Message.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    
    return render_template('worker_dashboard.html',
                           worker=current_user,
                           verified_skills=verified_skills,
                           recent_attempts=attempts,
                           inbox_count=inbox_count)


# ── PROFILE ───────────────────────────────────────────────────────────────────
@worker_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@worker_required
def profile():
    if request.method == 'POST':
        current_user.bio = request.form.get('bio', '').strip()
        current_user.location = request.form.get('location', '').strip()
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('worker.profile'))
    return render_template('worker_profile.html', worker=current_user)


# ── SKILL SELECTION ────────────────────────────────────────────────────────────
@worker_bp.route('/skills')
@login_required
@worker_required
def skill_selection():
    all_skills = Skill.query.order_by(Skill.category, Skill.name).all()
    taken_ids = {vs.skill_id for vs in VerifiedSkill.query.filter_by(user_id=current_user.id).all()}
    q_counts = {s.id: Question.query.filter_by(skill_id=s.id).count() for s in all_skills}
    attempt_counts = {}
    for s in all_skills:
        attempt_counts[s.id] = TestAttempt.query.filter_by(user_id=current_user.id, skill_id=s.id).count()
    
    return render_template('skill_selection.html',
                           skills=all_skills,
                           taken_ids=taken_ids,
                           q_counts=q_counts,
                           attempt_counts=attempt_counts)


# ── GAUNTLET TEST ──────────────────────────────────────────────────────────────
@worker_bp.route('/test/<int:skill_id>')
@login_required
@worker_required
def gauntlet_test(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    if VerifiedSkill.query.filter_by(user_id=current_user.id, skill_id=skill_id).first():
        flash('You already have a verified certificate for this skill.', 'warning')
        return redirect(url_for('worker.skill_selection'))
    
    all_qs = Question.query.filter_by(skill_id=skill_id).all()
    if not all_qs:
        flash('No questions available for this skill yet.', 'warning')
        return redirect(url_for('worker.skill_selection'))
    
    selected = random.sample(all_qs, min(10, len(all_qs)))
    session[f'test_qs_{skill_id}'] = [q.id for q in selected]
    session[f'test_start_{skill_id}'] = datetime.utcnow().isoformat()
    
    return render_template('gauntlet_test.html', skill=skill, questions=selected)


# ── SUBMIT TEST ────────────────────────────────────────────────────────────────
@worker_bp.route('/test/<int:skill_id>/submit', methods=['POST'])
@login_required
@worker_required
def submit_test(skill_id):
    skill = Skill.query.get_or_404(skill_id)

    # Check already verified
    if VerifiedSkill.query.filter_by(user_id=current_user.id, skill_id=skill_id).first():
        flash('Already verified for this skill.', 'warning')
        return redirect(url_for('worker.dashboard'))

    # Recover question IDs from session
    q_ids = session.get(f'test_qs_{skill_id}')
    if not q_ids:
        flash('Session expired. Please retake the test.', 'danger')
        return redirect(url_for('worker.skill_selection'))

    questions = Question.query.filter(Question.id.in_(q_ids)).all()
    total = len(questions)
    correct = 0
    results = []

    for q in questions:
        chosen = request.form.get(f'q_{q.id}', '').upper().strip()
        is_right = chosen == q.correct_answer
        if is_right:
            correct += 1
        results.append({
            'question': q.question_text,
            'your_answer': chosen if chosen else '(No answer)',
            'correct_answer': q.correct_answer,
            'options': {'A': q.option_a, 'B': q.option_b,
                       'C': q.option_c, 'D': q.option_d},
            'is_correct': is_right,
        })

    score = round((correct / total) * 100, 2) if total else 0.0
    passed = score >= 50
    ts = datetime.utcnow()
    sk_hash = generate_skill_hash(current_user.id, skill_id, score, ts.isoformat())

    # Record attempt
    db.session.add(TestAttempt(
        user_id=current_user.id, skill_id=skill_id,
        score=score, passed=passed, taken_at=ts
    ))

    # Record verified skill
    vs = VerifiedSkill(user_id=current_user.id, skill_id=skill_id,
                       score=score, skill_hash=sk_hash, verified_at=ts)
    db.session.add(vs)

    # Recalculate aggregate scores
    _recalc_scores(current_user)
    db.session.commit()

    # Clean session
    session.pop(f'test_qs_{skill_id}', None)
    session.pop(f'test_start_{skill_id}', None)

    return render_template('test_results.html',
                           skill=skill, score=score,
                           correct=correct, total=total,
                           results=results, skill_hash=sk_hash,
                           ts=ts, passed=passed)

    # Record attempt
    db.session.add(TestAttempt(
        user_id=current_user.id, skill_id=skill_id,
        score=score, passed=passed, taken_at=ts
    ))

    # Record verified skill
    vs = VerifiedSkill(user_id=current_user.id, skill_id=skill_id,
                       score=score, skill_hash=sk_hash, verified_at=ts)
    db.session.add(vs)

    # Recalculate aggregate scores
    _recalc_scores(current_user)
    db.session.commit()

    # Clean session
    session.pop(f'test_qs_{skill_id}', None)
    session.pop(f'test_start_{skill_id}', None)

    return render_template('test_results.html',
                           skill=skill, score=score,
                           correct=correct, total=total,
                           results=results, skill_hash=sk_hash,
                           ts=ts, passed=passed)


# ── PASSPORT ──────────────────────────────────────────────────────────────────
@worker_bp.route('/passport')
@login_required
@worker_required
def passport():
    vs_list = VerifiedSkill.query.filter_by(user_id=current_user.id)\
                    .order_by(VerifiedSkill.score.desc()).all()
    
    verified = []
    for v in vs_list:
        skill = Skill.query.get(v.skill_id)
        if skill:
            verified.append({'name': skill.name, 'score': v.score, 'hash': v.skill_hash})
    
    passport_url = url_for('worker.public_passport',
                           anon_id=current_user.anonymous_id, _external=True)
    qr_b64 = _make_qr(passport_url)
    
    return render_template('passport.html',
                           worker=current_user,
                           verified=verified,
                           qr_b64=qr_b64,
                           public=False,
                           passport_url=passport_url)


@worker_bp.route('/passport/<anon_id>')
def public_passport(anon_id):
    user = User.query.filter_by(anonymous_id=anon_id, role='worker').first_or_404()
    vs_list = VerifiedSkill.query.filter_by(user_id=user.id)\
                  .order_by(VerifiedSkill.score.desc()).all()
    
    verified = []
    for v in vs_list:
        skill = Skill.query.get(v.skill_id)
        if skill:
            verified.append({'name': skill.name, 'score': v.score, 'hash': v.skill_hash})
    
    return render_template('passport.html',
                           worker=user,
                           verified=verified,
                           qr_b64=None,
                           public=True,
                           anon_user=user)


# ── LEADERBOARD ────────────────────────────────────────────────────────────────
@worker_bp.route('/leaderboard')
@login_required
@worker_required
def leaderboard():
    top_workers = User.query.filter_by(role='worker')\
                      .order_by(User.shadow_score.desc()).limit(20).all()
    my_rank = None
    all_workers = User.query.filter_by(role='worker')\
                      .order_by(User.shadow_score.desc()).all()
    for i, w in enumerate(all_workers, 1):
        if w.id == current_user.id:
            my_rank = i
            break
    
    skill_leaders = {}
    for skill in Skill.query.all():
        top = VerifiedSkill.query.filter_by(skill_id=skill.id)\
                  .order_by(VerifiedSkill.score.desc()).first()
        if top:
            worker = User.query.get(top.user_id)
            skill_leaders[skill.name] = {
                'anon_id': worker.anonymous_id if worker else 'Unknown',
                'score': top.score
            }
    
    return render_template('leaderboard.html',
                           top_workers=top_workers,
                           my_rank=my_rank,
                           total_workers=len(all_workers),
                           skill_leaders=skill_leaders)


# ── INBOX ──────────────────────────────────────────────────────────────────────
@worker_bp.route('/inbox')
@login_required
@worker_required
def inbox():
    messages = Message.query.filter_by(receiver_id=current_user.id)\
                   .order_by(Message.sent_at.desc()).all()
    # Mark all as read
    for m in messages:
        if not m.is_read:
            m.is_read = True
    db.session.commit()
    return render_template('worker_inbox.html', messages=messages)