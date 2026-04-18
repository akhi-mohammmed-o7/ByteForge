"""Complete seed data: 5 skills with 10 questions each + demo data."""
from models import db, User, Skill, Question, VerifiedSkill
from werkzeug.security import generate_password_hash
from utils.hash_generator import generate_anonymous_id, generate_skill_hash
from datetime import datetime

SKILLS = [
    ("Python Programming", "Technology", "fa-python"),
    ("Data Analysis", "Technology", "fa-chart-bar"),
    ("Web Development", "Technology", "fa-globe"),
    ("SQL & Databases", "Technology", "fa-database"),
    ("Communication Skills", "Soft Skills", "fa-comments"),
]

QUESTIONS = {
    "Python Programming": [
        ("What is the output of print(type([]))?", "<class 'dict'>", "<class 'list'>", "<class 'tuple'>", "<class 'set'>", "B"),
        ("Which keyword defines a function in Python?", "func", "define", "def", "function", "C"),
        ("What does len('hello') return?", "4", "5", "6", "None", "B"),
        ("Which is an immutable data type?", "list", "set", "dict", "tuple", "D"),
        ("How to open a file for reading?", "open('f','w')", "open('f','r')", "open('f','a')", "file.open('f')", "B"),
        ("What does range(3) produce?", "[1,2,3]", "[0,1,2,3]", "[0,1,2]", "[1,2]", "C"),
        ("Exponentiation operator in Python?", "^", "**", "//", "%%", "B"),
        ("What does list.append(x) do?", "Insert at index 0", "Remove x", "Add to end", "Sort list", "C"),
        ("What is a lambda function?", "Named function", "Anonymous inline function", "Class method", "Recursive function", "B"),
        ("Module for regex in Python?", "regex", "re", "regexp", "string", "B"),
    ],
    "Data Analysis": [
        ("Which library provides DataFrame?", "NumPy", "Matplotlib", "Pandas", "Seaborn", "C"),
        ("What does df.dropna() do?", "Fills missing values", "Removes rows with missing values", "Renames columns", "Sorts data", "B"),
        ("Mean of [4,8,6,5,3,2,8,9,2,5]?", "5.0", "5.2", "5.8", "6.0", "B"),
        ("Best chart for distribution?", "Bar chart", "Pie chart", "Histogram", "Line chart", "C"),
        ("What does df.groupby('col').mean() compute?", "Total sum", "Row count", "Average per group", "Maximum", "C"),
        ("Correlation of -1 means?", "No correlation", "Perfect positive", "Perfect negative", "Weak correlation", "C"),
        ("Function to merge DataFrames?", "concat()", "merge()", "append()", "join_on()", "B"),
        ("What is an outlier?", "Most common value", "Median", "Value significantly distant", "Null value", "C"),
        ("df.describe() returns?", "Column names", "First 5 rows", "Summary statistics", "Data types", "C"),
        ("Data normalization is?", "Removing duplicates", "Scaling to standard range", "Sorting data", "Converting strings", "B"),
    ],
    "Web Development": [
        ("HTML stands for?", "Hyper Text Markup Language", "High Tech Modern Language", "Hyperlink Text Markup", "Home Tool Markup", "A"),
        ("CSS property for text size?", "text-size", "font-size", "text-style", "font-weight", "B"),
        ("Purpose of <meta charset='UTF-8'>?", "Sets title", "Character encoding", "Links CSS", "Viewport", "B"),
        ("HTTP method to send data?", "GET", "PUT", "POST", "HEAD", "C"),
        ("CSS flexbox helps with?", "3D animations", "1D layout alignment", "Database queries", "Server routing", "B"),
        ("localStorage.setItem() does?", "Sends to server", "Stores in browser", "Creates cookie", "Writes to DB", "B"),
        ("REST API is?", "JS framework", "Styling method", "API architecture", "Query language", "C"),
        ("Tag for unordered list?", "<ol>", "<li>", "<ul>", "<list>", "C"),
        ("CSS z-index controls?", "Transparency", "Stacking order", "Font size", "Animation", "B"),
        ("Responsive design means?", "Mobile only", "Adapts to screen sizes", "Fast loading", "With animations", "B"),
    ],
    "SQL & Databases": [
        ("SQL statement to retrieve data?", "GET", "FETCH", "SELECT", "PULL", "C"),
        ("WHERE clause does?", "Groups rows", "Filters rows", "Sorts results", "Joins tables", "B"),
        ("Removes duplicates?", "UNIQUE", "DISTINCT", "FILTER", "DIFFERENT", "B"),
        ("PRIMARY KEY is?", "Foreign reference", "Unique identifier", "Indexed column", "Nullable", "B"),
        ("JOIN does?", "Deletes records", "Combines tables", "Creates table", "Updates values", "B"),
        ("Count rows function?", "SUM()", "AVG()", "COUNT()", "MAX()", "C"),
        ("Normalization is?", "Backup data", "Encrypt columns", "Reduce redundancy", "Index columns", "C"),
        ("GROUP BY does?", "Filters before", "Groups for aggregation", "Sorts results", "Joins tables", "B"),
        ("Remove table permanently?", "DELETE TABLE", "REMOVE TABLE", "DROP TABLE", "TRUNCATE", "C"),
        ("FOREIGN KEY is?", "Primary key copy", "Reference to PK", "Auto-increment", "Encrypted", "B"),
    ],
    "Communication Skills": [
        ("Active listening is?", "Waiting to speak", "Full concentration and understanding", "Listening to music", "Nodding without listening", "B"),
        ("Non-verbal communication?", "Writing emails", "Body language and gestures", "Sign language only", "Speaking quietly", "B"),
        ("Purpose of executive summary?", "Full technical details", "Brief overview of document", "List all references", "Describe methodology only", "B"),
        ("Empathy in communication?", "Feeling sorry for someone", "Understanding and sharing feelings", "Agreeing with everything", "Being polite", "B"),
        ("Assertive communication style?", "Aggressive and demanding", "Passive and avoiding", "Clear and respectful", "Manipulating others", "C"),
        ("Constructive feedback is?", "Harsh criticism", "Vague suggestions", "Specific and actionable", "Only positive comments", "C"),
        ("What is paraphrasing?", "Copying exactly", "Restating in own words", "Interrupting speaker", "Summarizing negatives", "B"),
        ("Open-ended questions?", "Get yes/no answers", "Encourage detailed responses", "Close conversation", "Test facts only", "B"),
        ("Tone of voice affects?", "Nothing important", "Message perception", "Grammar only", "Length of talk", "B"),
        ("Best way to handle conflict?", "Avoid it completely", "Blame others", "Listen and find solution", "Be aggressive", "C"),
    ],
}

def seed_all(app):
    with app.app_context():
        # Admin
        if not User.query.filter_by(email='admin@pramaan.io').first():
            db.session.add(User(
                name='ByteForge Admin',
                email='admin@pramaan.io',
                password_hash=generate_password_hash('Admin@123'),
                role='admin'
            ))
            print("[✓] Admin created")

        # Demo employers
        employers = [
            ('TechCorp Solutions', 'hr@techcorp.io', 'Employer@123'),
            ('GrowthHive Agency', 'talent@growthhive.io', 'Employer@123'),
        ]
        for name, email, pw in employers:
            if not User.query.filter_by(email=email).first():
                db.session.add(User(
                    name=name, email=email,
                    password_hash=generate_password_hash(pw),
                    role='employer'
                ))
                print(f"[✓] Employer: {email}")

        # Demo worker
        if not User.query.filter_by(email='worker@demo.com').first():
            worker = User(
                name='Demo Worker',
                email='worker@demo.com',
                password_hash=generate_password_hash('worker123'),
                role='worker',
                anonymous_id=generate_anonymous_id(),
                shadow_score=0.0,
                trust_score=0.0
            )
            db.session.add(worker)
            print("[✓] Demo worker: worker@demo.com / worker123")

        db.session.commit()

        # Skills
        skill_map = {}
        for sname, scat, sicon in SKILLS:
            existing = Skill.query.filter_by(name=sname).first()
            if existing:
                skill_map[sname] = existing
            else:
                s = Skill(name=sname, category=scat, icon=sicon)
                db.session.add(s)
                db.session.flush()
                skill_map[sname] = s
                print(f"[✓] Skill: {sname}")

        # Questions
        for skill_name, qs in QUESTIONS.items():
            skill = skill_map.get(skill_name)
            if skill and Question.query.filter_by(skill_id=skill.id).count() == 0:
                for qt, oa, ob, oc, od, ans in qs:
                    db.session.add(Question(
                        skill_id=skill.id,
                        question_text=qt,
                        option_a=oa, option_b=ob,
                        option_c=oc, option_d=od,
                        correct_answer=ans
                    ))
                print(f"[✓] {len(qs)} questions for {skill_name}")

        db.session.commit()
        
        # Add demo verified skill for worker
        worker = User.query.filter_by(email='worker@demo.com').first()
        if worker:
            python_skill = Skill.query.filter_by(name='Python Programming').first()
            if python_skill and not VerifiedSkill.query.filter_by(user_id=worker.id, skill_id=python_skill.id).first():
                vs = VerifiedSkill(
                    user_id=worker.id,
                    skill_id=python_skill.id,
                    score=85.0,
                    skill_hash=generate_skill_hash(worker.id, python_skill.id, 85.0),
                    verified_at=datetime.utcnow()
                )
                db.session.add(vs)
                worker.shadow_score = 85.0
                worker.trust_score = 255.0
                db.session.commit()
                print("[✓] Added demo verified skill for worker")
                
        print("\n[✓] Database seeding complete!\n")