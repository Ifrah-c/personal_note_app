 # Step 1: Project Setup & Database Models (Personal Note-Taking App)

from flask import Flask,render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash,check_password_hash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SECRET_KEY'] = 'your_secret_key'  

# Initialize the database
db = SQLAlchemy(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)
    notes = db.relationship('Note', backref='owner', lazy=True)

# Note Model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_pw = generate_password_hash(password)
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!')
            return redirect(url_for('signup'))
        new_user = User(username=username, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Signup successful. Please log in.')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        flash('Invalid credentials')
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please log in to view your notes.')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    notes = Note.query.filter_by(owner=user).order_by(Note.date_created.desc()).all()
    return render_template('dashboard.html', user=user, notes=notes)


@app.route('/add', methods=['GET', 'POST'])
def add_note():
    if 'user_id' not in session:
        flash('Please log in to add a note.')
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        new_note = Note(title=title, content=content, user_id=session['user_id'])
        db.session.add(new_note)
        db.session.commit()
        flash('Note added successfully!')
        return redirect(url_for('dashboard'))

    return render_template('add_note.html')


@app.route('/edit/<int:note_id>', methods=['GET', 'POST'])
def edit_note(note_id):
    if 'user_id' not in session:
        flash('Please log in to edit notes.')
        return redirect(url_for('login'))

    note = Note.query.get_or_404(note_id)

    if note.user_id != session['user_id']:
        flash('You do not have permission to edit this note.')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        note.title = request.form['title']
        note.content = request.form['content']
        db.session.commit()
        flash('Note updated successfully!')
        return redirect(url_for('dashboard'))

    return render_template('edit_note.html', note=note)

@app.route('/delete/<int:note_id>')
def delete_note(note_id):
    if 'user_id' not in session:
        flash('Please log in to delete notes.')
        return redirect(url_for('login'))

    note = Note.query.get_or_404(note_id)

    if note.user_id != session['user_id']:
        flash('You do not have permission to delete this note.')
        return redirect(url_for('dashboard'))

    db.session.delete(note)
    db.session.commit()
    flash('Note deleted successfully!')
    return redirect(url_for('dashboard'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
