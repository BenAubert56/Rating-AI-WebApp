from datetime import datetime
from flask import jsonify, render_template, request, redirect, url_for, flash, session
from sqlalchemy import and_, asc, or_
from app import app, db, bcrypt, login_manager
from app.models import Product, User, Comment, Service, Role
from functools import wraps

ADMIN = "Admin"

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

@app.route('/access_denied')
def access_denied():
    return render_template('access_denied.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    roles = Role.query.all()  # Récupérer tous les rôles depuis la base de données

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role_name = request.form['role']

        # Vérifier si l'utilisateur existe déjà
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose another one.', 'danger')
            return redirect(url_for('register'))

        # Vérifier si les mots de passe correspondent
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('register'))

        role = Role.query.filter_by(name=role_name).first()
        if not role:
            flash('Invalid role selected!')
            return redirect(url_for('register'))

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username, password=hashed_password, role=role)

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

    return render_template('register.html', roles=[role.name for role in roles])

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
        user_id = session.get('user_id')
        current_user = User.query.filter(
                User.id == user_id
        ).first()
        role = Role.query.filter(
            Role.id == current_user.role_id
        ).first()
        is_admin = role.name == ADMIN
        products = Product.query.all()
        services = Service.query.all()
        return render_template('index.html', products=products, services=services, is_admin=is_admin)
    else:
        return redirect(url_for('login'))

@app.route('/add_comment/<item_type>/<int:item_id>', methods=['POST'])
@session_login_required
def add_comment(item_type, item_id):
    content = request.form['content']
    user_id = 1  # Remplacez par l'ID de l'utilisateur connecté
    if item_type == 'product':
        comment = Comment(content=content, user_id=user_id, product_id=item_id)
    elif item_type == 'service':
        comment = Comment(content=content, user_id=user_id, service_id=item_id)
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/view_comments/<item_type>/<int:item_id>', methods=['GET', 'POST'])
def view_comments(item_type, item_id):
    user_id = session.get('user_id')
    current_user = User.query.filter(
            User.id == user_id
    ).first()

    if item_type == 'product':
        item = Product.query.get_or_404(item_id)
        comments = db.session.query(Comment, User).join(User, Comment.user_id == User.id).filter(Comment.product_id == item_id).all()
    elif item_type == 'service':
        item = Service.query.get_or_404(item_id)
        comments = db.session.query(Comment, User).join(User, Comment.user_id == User.id).filter(Comment.service_id == item_id).all()

    if request.method == 'POST':
        content = request.form['content']
        new_comment = Comment(content=content, user_id=user_id, product_id=item_id if item_type == 'product' else None, service_id=item_id if item_type == 'service' else None)
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('view_comments', item_type=item_type, item_id=item_id))

    return render_template('view_comments.html', item=item, comments=comments, current_user=current_user)

@app.route('/add_item/<item_type>', methods=['GET', 'POST'])
@session_login_required
def add_item(item_type):
    user_id = session.get('user_id')
    current_user = User.query.filter(
            User.id == user_id
    ).first()
    if current_user.role.name != ADMIN:
        flash('You do not have permission to access this page.')
        return redirect(url_for('products_services'))
    
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        if item_type == 'product':
            item = Product(name=name, price=price)
        elif item_type == 'service':
            item = Service(name=name, price=price)
        db.session.add(item)
        db.session.commit()
        flash(f'{item_type.capitalize()} added successfully!')
        return redirect(url_for('products_services'))
    
    return render_template('add_item.html', item_type=item_type)

@app.route('/edit_item/<item_type>/<int:item_id>', methods=['GET', 'POST'])
@session_login_required
def edit_item(item_type, item_id):
    user_id = session.get('user_id')
    current_user = User.query.filter(
            User.id == user_id
    ).first()
    if current_user.role.name != ADMIN:
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    
    if item_type == 'product':
        item = Product.query.get_or_404(item_id)
    elif item_type == 'service':
        item = Service.query.get_or_404(item_id)
    
    if request.method == 'POST':
        item.name = request.form['name']
        item.price = request.form['price']
        db.session.commit()
        flash(f'{item_type.capitalize()} updated successfully!')
        return redirect(url_for('index'))
    
    return render_template('edit_item.html', item=item, item_type=item_type)

@app.route('/delete_item/<item_type>/<int:item_id>', methods=['POST'])
@session_login_required
def delete_item(item_type, item_id):
    user_id = session.get('user_id')
    current_user = User.query.filter(
            User.id == user_id
    ).first()
    if current_user.role.name != ADMIN:
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    
    if item_type == 'product':
        item = Product.query.get_or_404(item_id)
    elif item_type == 'service':
        item = Service.query.get_or_404(item_id)
    
    db.session.delete(item)
    db.session.commit()
    flash(f'{item_type.capitalize()} deleted successfully!')
    return redirect(url_for('index'))