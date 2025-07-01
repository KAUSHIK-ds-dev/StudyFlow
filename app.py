from flask import Flask, render_template, request, redirect, session, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
from flask import send_from_directory

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kaushik'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///study_management.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure upload directory exists

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class Student(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    academic_info = db.Column(db.Text)
    user_type = db.Column(db.String(20), default='student')
    
    applications = db.relationship('Application', backref='student', lazy=True)
    documents = db.relationship('Document', backref='student', lazy=True)
    test_scores = db.relationship('TestScore', backref='student', lazy=True)
    lor_requests = db.relationship('LORRequest', backref='student', lazy=True)

    def get_id(self):
        return f"student-{self.id}"

class Faculty(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), default='faculty')
    
    lor_requests = db.relationship('LORRequest', backref='faculty', lazy=True)
    def get_id(self):
        return f"faculty-{self.id}"
    

class University(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    ranking = db.Column(db.Integer)
    website = db.Column(db.String(200))
    
    programs = db.relationship('Program', backref='university', lazy=True)

class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    university_id = db.Column(db.Integer, db.ForeignKey('university.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.Date, nullable=False)
    duration = db.Column(db.String(50))
    tuition_fees = db.Column(db.Float)
    course_type = db.Column(db.String(100))
    
    applications = db.relationship('Application', backref='program', lazy=True)

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)
    status = db.Column(db.String(50), default='Draft')
    applied_date = db.Column(db.Date)
    decision_date = db.Column(db.Date)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    file_path = db.Column(db.String(200))
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

class LORRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    status = db.Column(db.String(50), default='Pending')
    upload_path = db.Column(db.String(200))
    request_date = db.Column(db.DateTime, default=datetime.utcnow)

class TestScore(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    test_type = db.Column(db.String(50), nullable=False)
    score = db.Column(db.String(20), nullable=False)
    date_taken = db.Column(db.Date, nullable=False)

class Scholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    eligibility = db.Column(db.Text)
    link = db.Column(db.String(200))
    country = db.Column(db.String(100))
    field = db.Column(db.String(100))

class SavedScholarship(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    scholarship_id = db.Column(db.Integer, db.ForeignKey('scholarship.id'), nullable=False)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form['user_type']
        
        if user_type == 'student':
            user = Student.query.filter_by(email=email).first()
        elif user_type == 'faculty':
            user = Faculty.query.filter_by(email=email).first()
        else:  # admin
            user = Student.query.filter_by(email=email, user_type='admin').first()
        
        if user and check_password_hash(user.password, password):
           
            login_user(user)
            session['user_type'] = user.user_type
            session['user_id'] = user.id

            if user.user_type == 'admin':
                return redirect(url_for('admin_panel'))
            elif user.user_type == 'faculty':
                return redirect(url_for('faculty_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password')
    
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        phone = request.form.get('phone', '')
        user_type = request.form['user_type']
        
        # Check if user already exists
        existing_user = Student.query.filter_by(email=email).first() or Faculty.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        
        if user_type == 'student':
            user = Student(name=name, email=email, password=hashed_password, phone=phone)
        else:  # faculty
            user = Faculty(name=name, email=email, password=hashed_password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith("student-"):
        return Student.query.get(int(user_id.split("-")[1]))
    elif user_id.startswith("faculty-"):
        return Faculty.query.get(int(user_id.split("-")[1]))

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('user_type') != 'student':
        return redirect(url_for('index'))
    
    # Get student's applications
    applications = Application.query.filter_by(student_id=session.get('user_id')).all()
    
    # Get upcoming deadlines
    upcoming_deadlines = []
    for app in applications:
        if app.program.deadline >= date.today():
            upcoming_deadlines.append({
                'program': app.program.name,
                'university': app.program.university.name,
                'deadline': app.program.deadline,
                'status': app.status
            })
    
    # Sort by deadline
    upcoming_deadlines.sort(key=lambda x: x['deadline'])
    
    return render_template('dashboard.html', 
                         applications=applications, 
                         upcoming_deadlines=upcoming_deadlines[:5],today=date.today())

@app.route('/universities')
@login_required
def universities():
    # Get filter parameters
    country = request.args.get('country', '')
    course_type = request.args.get('course_type', '')
    max_tuition = request.args.get('max_tuition', '')
    
    # Build query
    query = db.session.query(Program).join(University)
    
    if country:
        query = query.filter(University.country.ilike(f'%{country}%'))
    if course_type:
        query = query.filter(Program.course_type.ilike(f'%{course_type}%'))
    if max_tuition:
        query = query.filter(Program.tuition_fees <= float(max_tuition))
    
    programs = query.all()
    
    # Get unique countries and course types for filters
    countries = db.session.query(University.country).distinct().all()
    course_types = db.session.query(Program.course_type).distinct().all()
    
    return render_template('universities.html', 
                         programs=programs, 
                         countries=[c[0] for c in countries if c[0]], 
                         course_types=[ct[0] for ct in course_types if ct[0]])

@app.route('/program/<int:program_id>')
@login_required
def program_detail(program_id):
    program = Program.query.get_or_404(program_id)
    today = date.today()
    return render_template('program_detail.html', program=program,today=today)

@app.route('/apply/<int:program_id>')
@login_required
def apply_program(program_id):
    if current_user.user_type != 'student':
        return redirect(url_for('index'))
    
    # Check if already applied
    existing_app = Application.query.filter_by(student_id=current_user.id, program_id=program_id).first()
    if existing_app:
        flash('You have already applied to this program')
        return redirect(url_for('program_detail', program_id=program_id))
    
    application = Application(student_id=current_user.id, program_id=program_id)
    db.session.add(application)
    db.session.commit()
    
    flash('Application saved as draft')
    return redirect(url_for('applications'))

@app.route('/applications')
@login_required
def applications():
    if current_user.user_type != 'student':
        return redirect(url_for('index'))
    
    applications = Application.query.filter_by(student_id=current_user.id).all()
    today = date.today()
    return render_template('applications.html', applications=applications,today=today)

@app.route('/update_application/<int:app_id>', methods=['POST'])
@login_required
def update_application(app_id):
    application = Application.query.get_or_404(app_id)
    if application.student_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    new_status = request.json.get('status')
    application.status = new_status
    
    if new_status == 'Submitted':
        application.applied_date = date.today()
    
    db.session.commit()
    return jsonify({'success': True})

@app.route('/delete_application/<int:app_id>', methods=['DELETE'])
def delete_application(app_id):
    app_to_delete = Application.query.get(app_id)
    if app_to_delete:
        db.session.delete(app_to_delete)
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Application not found'}), 404

@app.route('/documents')
@login_required
def documents():
    faculties = Faculty.query.all()  # 👈 send list of all faculties
    return render_template('documents.html', faculties=faculties)


@app.route('/upload_document', methods=['POST'])
@login_required
def upload_document():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('documents'))
    
    file = request.files['file']
    doc_type = request.form['type']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('documents'))
    
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        document = Document(student_id=current_user.id, type=doc_type, file_path=filename)
        db.session.add(document)
        db.session.commit()
        
        flash('Document uploaded successfully')
    
    return redirect(url_for('documents'))

@app.route('/test_scores')
@login_required
def test_scores():
    if current_user.user_type != 'student':
        return redirect(url_for('index'))
    
    scores = TestScore.query.filter_by(student_id=current_user.id).all()
    return render_template('test_scores.html', scores=scores)

@app.route('/add_test_score', methods=['POST'])
@login_required
def add_test_score():
    test_type = request.form['test_type']
    score = request.form['score']
    date_taken = datetime.strptime(request.form['date_taken'], '%Y-%m-%d').date()
    
    test_score = TestScore(student_id=current_user.id, test_type=test_type, score=score, date_taken=date_taken)
    db.session.add(test_score)
    db.session.commit()
    
    flash('Test score added successfully')
    return redirect(url_for('test_scores'))

@app.route('/delete_score/<int:score_id>', methods=['DELETE'])
def delete_score(score_id):
    score = TestScore.query.get(score_id)
    if not score:
        return jsonify({'success': False, 'message': 'Score not found'}), 404

    db.session.delete(score)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/edit_score/<int:score_id>', methods=['POST'])
def edit_score(score_id):
    score = TestScore.query.get(score_id)
    if not score:
        return jsonify({'success': False, 'message': 'Score not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'No JSON data received'}), 400

    try:
        score.test_type = data['test_type']
        score.score = data['score']
        score.date_taken = datetime.strptime(data['date_taken'], '%Y-%m-%d')

        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    
@app.route('/scholarships')
@login_required
def scholarships():
    country = request.args.get('country', '')
    field = request.args.get('field', '')
    
    query = Scholarship.query
    
    if country:
        query = query.filter(Scholarship.country.ilike(f'%{country}%'))
    if field:
        query = query.filter(Scholarship.field.ilike(f'%{field}%'))
    
    scholarships = query.all()
    
    # Get saved scholarships for current user
    saved_scholarships = []
    if current_user.user_type == 'student':
        saved = SavedScholarship.query.filter_by(student_id=current_user.id).all()
        saved_scholarships = [s.scholarship_id for s in saved]
    
    return render_template('scholarships.html', 
                         scholarships=scholarships, 
                         saved_scholarships=saved_scholarships)

@app.route('/save_scholarship/<int:scholarship_id>')
@login_required
def save_scholarship(scholarship_id):
    if current_user.user_type != 'student':
        return redirect(url_for('scholarships'))
    
    # Check if already saved
    existing = SavedScholarship.query.filter_by(student_id=current_user.id, scholarship_id=scholarship_id).first()
    if not existing:
        saved = SavedScholarship(student_id=current_user.id, scholarship_id=scholarship_id)
        db.session.add(saved)
        db.session.commit()
        flash('Scholarship saved to your list')
    else:
        flash('Scholarship already in your list')
    
    return redirect(url_for('scholarships'))

@app.route('/faculty_dashboard')
def faculty_dashboard():
    if current_user.user_type != 'faculty':
        return redirect(url_for('login'))

    lor_requests = LORRequest.query.filter_by(faculty_id=current_user.id).all()
    return render_template('faculty_dashboard.html', lor_requests=lor_requests, user=current_user)

@app.route('/request_lor', methods=['POST'])
@login_required
def request_lor():
    faculty_id = request.form.get('faculty_id')

    if not faculty_id:
        flash('Faculty not selected.')
        return redirect(url_for('documents'))

    existing_request = LORRequest.query.filter_by(student_id=current_user.id, faculty_id=faculty_id).first()
    if existing_request:
        flash('LOR already requested from this faculty.')
        return redirect(url_for('documents'))

    new_request = LORRequest(student_id=current_user.id, faculty_id=faculty_id)
    db.session.add(new_request)
    db.session.commit()

    flash('LOR request sent successfully.')
    return redirect(url_for('documents'))


@app.route('/upload_lor', methods=['POST'])
@login_required
def upload_lor():
    lor_id = request.form.get('lor_id')
    file = request.files.get('lor_file')
    comments = request.form.get('lor_comments')

    if not lor_id or not file:
        flash("Missing LOR ID or file.")
        return redirect(url_for('faculty_dashboard'))

    if file.filename == '':
        flash('No file selected.')
        return redirect(url_for('faculty_dashboard'))

    filename = secure_filename(file.filename)
    upload_dir = os.path.join('static', 'uploads', 'lors')
    os.makedirs(upload_dir, exist_ok=True)

    
    file.save(filename)  # ✅ Save the file once correctly

    lor = LORRequest.query.get(int(lor_id))
    if not lor:
        flash('LOR request not found.')
        return redirect(url_for('faculty_dashboard'))

    lor.upload_path = filename  # ✅ Only store the filename
    lor.status = 'Uploaded'
    db.session.commit()


    flash('LOR uploaded successfully.')
    return redirect(url_for('faculty_dashboard'))

@app.route('/uploads/lors/<filename>')
def uploaded_file(filename):
    ext = filename.rsplit('.', 1)[-1].lower()
    as_attachment = ext != 'pdf'
    return send_from_directory('static/uploads/lors', filename, as_attachment=True)


@app.route('/admin')
@login_required
def admin_panel():
    if current_user.user_type != 'admin':
        return redirect(url_for('index'))
    
    # Get statistics
    total_students = Student.query.filter_by(user_type='student').count()
    total_applications = Application.query.count()
    total_universities = University.query.count()
    total_programs = Program.query.count()
    
    
    # Get recent applications
    recent_applications = Application.query.order_by(Application.id.desc()).limit(10).all()
    all_universities = University.query.all()
    all_students = Student.query.filter_by(user_type='student').all()
    
    return render_template('admin.html', 
                         total_students=total_students,
                         total_applications=total_applications,
                         total_universities=total_universities,
                         total_programs=total_programs,
                         recent_applications=recent_applications,
                         all_universities=all_universities,
                         all_students=all_students)

@app.route('/admin/add_university', methods=['POST'])
@login_required
def add_university():
    if current_user.user_type != 'admin':
        return redirect(url_for('admin_panel'))

    name = request.form['name']
    country = request.form['country']
    ranking = request.form.get('ranking')
    website = request.form.get('website')

    new_uni = University(
        name=name,
        country=country,
        ranking=int(ranking) if ranking else None,
        website=website
    )
    db.session.add(new_uni)
    db.session.commit()
    return redirect(url_for('admin_panel'))


@app.route('/admin/add_program', methods=['POST'])
@login_required
def add_program():
    if current_user.user_type != 'admin':
        return redirect(url_for('admin_panel'))

    university_id = request.form['university_id']
    name = request.form['name']
    course_type = request.form['course_type']
    deadline = request.form['deadline']
    duration = request.form['duration']
    tuition_fees = request.form.get('tuition_fees')

    new_prog = Program(
        university_id=int(university_id),
        name=name,
        course_type=course_type,
        deadline=datetime.strptime(deadline, '%Y-%m-%d').date(),
        duration=duration,
        tuition_fees=float(tuition_fees) if tuition_fees else 0.0
    )
    db.session.add(new_prog)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/admin/update_status/<int:app_id>', methods=['POST'])
@login_required
def admin_update_status(app_id):
    if current_user.user_type != 'admin':
        return redirect(url_for('index'))

    application = Application.query.get_or_404(app_id)
    new_status = request.form.get('status')

    if new_status in ['Draft', 'Submitted', 'Accepted', 'Rejected']:
        application.status = new_status
        if new_status == 'Submitted' and not application.applied_date:
            application.applied_date = date.today()
        db.session.commit()

    return redirect(url_for('admin_panel'))

@app.route('/admin/application/<int:app_id>', methods=['GET', 'POST'])
@login_required
def admin_view_application(app_id):
    if current_user.user_type != 'admin':
        return redirect(url_for('index'))

    application = Application.query.get_or_404(app_id)

    if request.method == 'POST':
        new_status = request.form.get('status')
        if new_status in ['Draft', 'Submitted', 'Accepted', 'Rejected']:
            application.status = new_status
            if new_status == 'Submitted' and not application.applied_date:
                application.applied_date = date.today()
            db.session.commit()
            flash('Status updated successfully.')
        return redirect(url_for('admin_view_application', app_id=app_id))

    return render_template('admin_application_detail.html', app=application)

@app.route('/admin/report/documents')
@login_required
def admin_documents_report():
    if current_user.user_type != 'admin':
        return redirect(url_for('index'))

    documents = Document.query.order_by(Document.upload_date.desc()).all()
    return render_template('admin_documents_report.html', documents=documents)

@app.route('/uploads/<filename>')
def uploaded_document(filename):
    full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(f"[DEBUG] Document requested: {full_path}")

    if not os.path.exists(full_path):
        print(f"[ERROR] File not found: {full_path}")
        return "File not found", 404

    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

def init_db():
    """Initialize database with sample data"""
    db.create_all()
    
    # Create admin user if not exists
    admin = Student.query.filter_by(email='admin@example.com').first()
    if not admin:
        admin = Student(
            name='Admin User',
            email='admin@example.com',
            password=generate_password_hash('admin123'),
            user_type='admin'
        )
        db.session.add(admin)
    
    # Add sample universities and programs
    if University.query.count() == 0:
        universities_data = [
            {'name': 'Harvard University', 'country': 'USA', 'ranking': 1, 'website': 'https://harvard.edu'},
            {'name': 'Stanford University', 'country': 'USA', 'ranking': 2, 'website': 'https://stanford.edu'},
            {'name': 'MIT', 'country': 'USA', 'ranking': 3, 'website': 'https://mit.edu'},
            {'name': 'University of Oxford', 'country': 'UK', 'ranking': 4, 'website': 'https://ox.ac.uk'},
            {'name': 'University of Cambridge', 'country': 'UK', 'ranking': 5, 'website': 'https://cam.ac.uk'},
        ]
        
        for uni_data in universities_data:
            uni = University(**uni_data)
            db.session.add(uni)
        
        db.session.commit()
        
        # Add sample programs
        programs_data = [
            {'university_id': 1, 'name': 'Computer Science MS', 'deadline': date(2024, 12, 15), 'duration': '2 years', 'tuition_fees': 50000, 'course_type': 'Masters'},
            {'university_id': 1, 'name': 'MBA', 'deadline': date(2025, 11, 30), 'duration': '2 years', 'tuition_fees': 70000, 'course_type': 'Masters'},
            {'university_id': 2, 'name': 'Data Science MS', 'deadline': date(2024, 12, 1), 'duration': '2 years', 'tuition_fees': 55000, 'course_type': 'Masters'},
            {'university_id': 3, 'name': 'AI PhD', 'deadline': date(2024, 12, 15), 'duration': '4-5 years', 'tuition_fees': 0, 'course_type': 'PhD'},
            {'university_id': 4, 'name': 'Engineering MS', 'deadline': date(2025, 1, 15), 'duration': '1 year', 'tuition_fees': 35000, 'course_type': 'Masters'},
        ]
        
        for prog_data in programs_data:
            prog = Program(**prog_data)
            db.session.add(prog)
    
    # Add sample scholarships
    if Scholarship.query.count() == 0:
        scholarships_data = [
            {'name': 'Fulbright Scholarship', 'description': 'Full funding for international students', 'eligibility': 'Outstanding academic record', 'link': 'https://fulbright.org', 'country': 'USA', 'field': 'All Fields'},
            {'name': 'Rhodes Scholarship', 'description': 'Study at Oxford University', 'eligibility': 'Leadership and academic excellence', 'link': 'https://rhodesscholar.org', 'country': 'UK', 'field': 'All Fields'},
            {'name': 'DAAD Scholarship', 'description': 'German Academic Exchange Service', 'eligibility': 'Good academic standing', 'link': 'https://daad.de', 'country': 'Germany', 'field': 'All Fields'},
        ]
        
        for schol_data in scholarships_data:
            schol = Scholarship(**schol_data)
            db.session.add(schol)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(debug=True)
