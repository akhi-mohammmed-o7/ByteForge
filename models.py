from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Index

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='worker', index=True)
    anonymous_id = db.Column(db.String(20), unique=True, nullable=True, index=True)
    shadow_score = db.Column(db.Float, default=0.0)
    trust_score = db.Column(db.Float, default=0.0)
    bio = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    verified_skills = db.relationship('VerifiedSkill', backref='worker', lazy=True, cascade='all, delete-orphan')
    shortlisted_by = db.relationship('Shortlist', foreign_keys='Shortlist.worker_id', backref='worker', lazy=True, cascade='all, delete-orphan')
    shortlisted = db.relationship('Shortlist', foreign_keys='Shortlist.employer_id', backref='employer', lazy=True, cascade='all, delete-orphan')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)

    def __repr__(self):
        return f'<User {self.anonymous_id or self.email}>'
    
    @property
    def verified_skills_count(self):
        return len(self.verified_skills)
    
    @property
    def average_score(self):
        if not self.verified_skills:
            return 0
        return sum(vs.score for vs in self.verified_skills) / len(self.verified_skills)


class Skill(db.Model):
    __tablename__ = 'skills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    category = db.Column(db.String(80), nullable=False, index=True)
    icon = db.Column(db.String(40), nullable=True, default='fa-code')
    
    questions = db.relationship('Question', backref='skill', lazy=True, cascade='all, delete-orphan')
    verified_skills = db.relationship('VerifiedSkill', backref='skill', lazy=True)
    
    def __repr__(self):
        return f'<Skill {self.name}>'
    
    @property
    def question_count(self):
        return len(self.questions)


class VerifiedSkill(db.Model):
    __tablename__ = 'verified_skills'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False)
    skill_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)
    verified_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_user_skill', 'user_id', 'skill_id'),
    )
    
    def __repr__(self):
        return f'<VerifiedSkill User:{self.user_id} Skill:{self.skill_id} Score:{self.score}>'


class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(400), nullable=False)
    option_b = db.Column(db.String(400), nullable=False)
    option_c = db.Column(db.String(400), nullable=False)
    option_d = db.Column(db.String(400), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    
    def __repr__(self):
        return f'<Question {self.id}: {self.question_text[:30]}...>'


class Shortlist(db.Model):
    __tablename__ = 'shortlists'
    id = db.Column(db.Integer, primary_key=True)
    employer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    worker_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    note = db.Column(db.Text, nullable=True)
    revealed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_employer_worker', 'employer_id', 'worker_id'),
    )
    
    def __repr__(self):
        return f'<Shortlist Employer:{self.employer_id} Worker:{self.worker_id}>'


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    subject = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, index=True)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<Message From:{self.sender_id} To:{self.receiver_id}>'
    
    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            db.session.commit()


class TestAttempt(db.Model):
    __tablename__ = 'test_attempts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False, index=True)
    score = db.Column(db.Float, nullable=False)
    passed = db.Column(db.Boolean, default=False)
    taken_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_user_skill_attempt', 'user_id', 'skill_id'),
    )
    
    def __repr__(self):
        return f'<TestAttempt User:{self.user_id} Skill:{self.skill_id} Score:{self.score}>'