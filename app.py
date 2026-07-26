import re
import json
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, User, Project, Question, Answer
import ai_service

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Ensure database tables exist
with app.app_context():
    db.create_all()

# Helper decorator for login protection
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Regex for basic email format validation
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validations
        if not name or not email or not password or not confirm_password:
            flash('All fields are required.', 'error')
            return render_template('signup.html')
            
        if not re.match(EMAIL_REGEX, email):
            flash('Invalid email format. Please enter a valid email address.', 'error')
            return render_template('signup.html')
            
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('signup.html')
            
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('signup.html')
            
        # Check if email exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists.', 'error')
            return render_template('signup.html')
            
        # Hash password and create user
        hashed_password = generate_password_hash(password)
        new_user = User(
            name=name,
            email=email,
            password_hash=hashed_password
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please sign in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            flash('Please fill in both fields.', 'error')
            return render_template('login.html')
            
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            # Create session
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    # Query projects belonging to user
    projects = Project.query.filter_by(user_id=user_id).order_by(Project.created_at.desc()).all()
    return render_template('dashboard.html', projects=projects)

@app.route('/project/new', methods=['GET', 'POST'])
@login_required
def new_project():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        domain = request.form.get('domain', '').strip()
        tech_stack = request.form.get('tech_stack', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validations
        if not title or not domain or not tech_stack or not description:
            flash('All project details are required.', 'error')
            return render_template('new_project.html')
            
        if len(description) < 50:
            flash('Please provide a more detailed description (at least 50 characters).', 'error')
            return render_template('new_project.html')
            
        user_id = session['user_id']
        
        # 1. Create and save Project model
        new_proj = Project(
            user_id=user_id,
            title=title,
            domain=domain,
            tech_stack=tech_stack,
            description=description
        )
        
        db.session.add(new_proj)
        db.session.flush() # gets project.id before committing
        
        # 2. Call AI Service to generate questions
        try:
            questions_list = ai_service.generate_questions(
                title=title,
                description=description,
                tech_stack=tech_stack,
                domain=domain
            )
            
            # If AI service doesn't return questions, create simple fallbacks
            if not questions_list:
                raise ValueError("No questions returned by the AI Examiner.")
                
            # Save generated questions
            for idx, q_info in enumerate(questions_list):
                q = Question(
                    project_id=new_proj.id,
                    question_text=q_info['text'],
                    category=q_info['category'],
                    order_index=idx
                )
                db.session.add(q)
                
            db.session.commit()
            flash('Project created and viva questions generated successfully!', 'success')
            return redirect(url_for('project_session', id=new_proj.id))
            
        except Exception as e:
            db.session.rollback()
            # Log error
            print(f"Error during AI generation or save: {str(e)}")
            flash(f"AI Service Error: {str(e)}. Please check your GEMINI_API_KEY environment variable.", "error")
            return render_template('new_project.html')
            
    return render_template('new_project.html')

@app.route('/project/<int:id>')
@login_required
def project_session(id):
    user_id = session['user_id']
    project = Project.query.get_or_404(id)
    
    # Security check: verify this project belongs to current logged-in user
    if project.user_id != user_id:
        flash('Access Denied: You do not own this project.', 'error')
        return redirect(url_for('dashboard'))
        
    return render_template('viva_session.html', project=project)

@app.route('/project/<int:id>/answer/<int:question_id>', methods=['POST'])
@login_required
def evaluate_question_answer(id, question_id):
    user_id = session['user_id']
    project = Project.query.get_or_404(id)
    
    # Security check
    if project.user_id != user_id:
        return jsonify({'error': 'Unauthorized access.'}), 403
        
    question = Question.query.filter_by(id=question_id, project_id=project.id).first_or_404()
    
    # Read student answer from request
    req_data = request.get_json() or {}
    student_answer = req_data.get('answer', '').strip()
    
    if not student_answer:
        return jsonify({'error': 'Answer text is empty.'}), 400
        
    # Construct project context
    project_context = (
        f"Title: {project.title}\n"
        f"Domain: {project.domain}\n"
        f"Tech Stack: {project.tech_stack}\n"
        f"Description: {project.description}"
    )
    
    try:
        # Call AI Evaluation service
        feedback_data = ai_service.evaluate_answer(
            project_context=project_context,
            question_text=question.question_text,
            student_answer=student_answer
        )
        
        # Serialize good, missing, improve to save as a single column JSON in DB
        serialized_feedback = json.dumps({
            'good': feedback_data['good'],
            'missing': feedback_data['missing'],
            'improve': feedback_data['improve']
        })
        
        # Check if an Answer already exists for this question
        existing_answer = Answer.query.filter_by(question_id=question.id).first()
        
        if existing_answer:
            # Update current practice attempt
            existing_answer.answer_text = student_answer
            existing_answer.feedback_text = serialized_feedback
            existing_answer.readiness_rating = feedback_data['rating']
            existing_answer.created_at = datetime.utcnow()
        else:
            # Create a new answer
            new_answer = Answer(
                question_id=question.id,
                answer_text=student_answer,
                feedback_text=serialized_feedback,
                readiness_rating=feedback_data['rating']
            )
            db.session.add(new_answer)
            
        db.session.commit()
        
        # Return response to front-end
        return jsonify({
            'good': feedback_data['good'],
            'missing': feedback_data['missing'],
            'improve': feedback_data['improve'],
            'rating': feedback_data['rating']
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error evaluating answer: {str(e)}")
        return jsonify({'error': f"Failed to call evaluation service: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)
