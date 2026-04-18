from flask import Blueprint, render_template, request
from models import VerifiedSkill, User

verify_bp = Blueprint('verify', __name__)

@verify_bp.route('/verify', methods=['GET', 'POST'])
def verify_public():
    result = None
    hash_input = request.form.get('hash_input', '').strip() if request.method == 'POST' else ''
    
    if request.method == 'POST' and hash_input:
        vs = VerifiedSkill.query.filter_by(skill_hash=hash_input).first()
        if vs:
            worker = User.query.get(vs.user_id)
            result = {
                'valid': True,
                'anonymous_id': worker.anonymous_id if worker else 'UNKNOWN',
                'skill_name': vs.skill.name,
                'category': vs.skill.category,
                'score': vs.score,
                'verified_at': vs.verified_at,
                'hash': vs.skill_hash,
            }
        else:
            result = {'valid': False, 'hash': hash_input}
    
    return render_template('verify_public.html', result=result, hash_input=hash_input)