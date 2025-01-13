from datetime import datetime
from flask import jsonify, render_template, request, redirect, url_for, flash, session
from sqlalchemy import and_, asc, or_
from app import app, db, bcrypt, login_manager
from app.models import Product, User, Comment
from functools import wraps

@app.before_request
def create_tables():
    db.create_all()

# Charger l'utilisateur depuis l'ID
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Décorateur pour routes protégées (session)
def session_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'danger')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.errorhandler(404)
def page_not_found(error):
    flash('Page not found!', 'danger')
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    flash('An unexpected error occurred!', 'danger')
    return render_template('500.html'), 500

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another one.', 'danger')
            return redirect(url_for('register'))

        # Vérifier si les mots de passe correspondent
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()  # Transaction explicite
        except Exception as e:
            db.session.rollback()  # En cas d'erreur, annuler la transaction
            flash('An error occurred while creating your account. Please try again.', 'danger')
            print(f"Error during registration: {e}")
            return redirect(url_for('register'))

        flash('Account created successfully! You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username

            # Log la connexion
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    user_id = session.get('user_id')
    if user_id:
        session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))   

@app.route('/')
@session_login_required
def index():
    current_user = session.get('username')
    if current_user:
        return render_template('index.html', message="t'es le plus beau")
    else:
        return redirect(url_for('login'))

