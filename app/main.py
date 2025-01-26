from datetime import date, datetime
from flask import json, jsonify, render_template, request, redirect, url_for, flash, session
from app import app, db, bcrypt, login_manager
from app.models import Product, User, Comment, Service, Role
from functools import wraps

from app.utils import predict_comment_rating

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
        if not current_user:
            flash('User not found!', 'danger')
            return redirect(url_for('login'))
        role = Role.query.filter(
            Role.id == current_user.role_id
        ).first()
        is_admin = role.name == ADMIN
        products = Product.query.all()
        services = Service.query.all()
        return render_template('index.html', products=products, services=services, is_admin=is_admin)
    else:
        return redirect(url_for('login'))

@app.route('/view_comments/<item_type>/<int:item_id>', methods=['GET', 'POST'])
def view_comments(item_type, item_id):
    user_id = session.get('user_id')
    current_user = User.query.filter(User.id == user_id).first()

    if item_type == 'product':
        item = Product.query.get_or_404(item_id)
        comments = db.session.query(Comment, User).join(User, Comment.user_id == User.id).filter(Comment.product_id == item_id).all()
    elif item_type == 'service':
        item = Service.query.get_or_404(item_id)
        comments = db.session.query(Comment, User).join(User, Comment.user_id == User.id).filter(Comment.service_id == item_id).all()

    if request.method == 'POST':
        content = request.form['content']
        rating = predict_comment_rating(content)
        user_id = current_user.id  # Utilisateur connecté
        date_posted = datetime.utcnow()
        if item_type == 'product':
            comment = Comment(content=content, rating=rating, date_posted=date_posted, user_id=user_id, product_id=item_id)
        elif item_type == 'service':
            comment = Comment(content=content, rating=rating, date_posted=date_posted, user_id=user_id, service_id=item_id)
        db.session.add(comment)
        db.session.commit()

        return redirect(url_for('view_comments', item_type=item_type, item_id=item_id))

    return render_template('view_comments.html', item=item, comments=comments, item_type=item_type, item_id=item_id)

@app.route('/add_item/<item_type>', methods=['GET', 'POST'])
@session_login_required
def add_item(item_type):
    user_id = session.get('user_id')
    current_user = User.query.filter(
            User.id == user_id
    ).first()
    if current_user.role.name != ADMIN:
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        date_posted = datetime.utcnow()
        if item_type == 'product':
            item = Product(name=name, price=price, date_posted=date_posted)
        elif item_type == 'service':
            item = Service(name=name, price=price)
        db.session.add(item)
        db.session.commit()
        flash(f'{item_type.capitalize()} added successfully!')
        return redirect(url_for('index'))
    
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
    current_user = User.query.filter(User.id == user_id).first()
    if current_user.role.name != 'Admin':
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

@app.route('/dashboard', methods=['GET', 'POST'])
@session_login_required
def dashbord():
    user_id = session.get('user_id')
    current_user = User.query.filter(User.id == user_id).first()
    if current_user.role.name != 'Admin':
        flash('You do not have permission to access this page.')
        return redirect(url_for('index'))

    comments = db.session.query(Comment, User).join(User, Comment.user_id == User.id).all()
    comments_with_items = []
    for comment, user in comments:
        if comment.product_id:
            item = Product.query.get(comment.product_id)
            item_type = 'product'
        elif comment.service_id:
            item = Service.query.get(comment.service_id)
            item_type = 'service'
        else:
            item = None
            item_type = None
        comments_with_items.append((comment, user, item, item_type))

    # Prepare data for average rating chart
    average_rating_data = {
        'labels': [],
        'data': []
    }
    products = Product.query.all()
    services = Service.query.all()
    for product in products:
        average_rating = db.session.query(db.func.avg(Comment.rating)).filter(Comment.product_id == product.id).scalar()
        average_rating_data['labels'].append(product.name)
        average_rating_data['data'].append(average_rating or 0)
    for service in services:
        average_rating = db.session.query(db.func.avg(Comment.rating)).filter(Comment.service_id == service.id).scalar()
        average_rating_data['labels'].append(service.name)
        average_rating_data['data'].append(average_rating or 0)

    # Prepare data for average comments per day chart
    average_comments_data = {
        'labels': [],
        'data': []
    }
    comments_per_day = db.session.query(db.func.date(Comment.date_posted), db.func.count(Comment.id)).group_by(db.func.date(Comment.date_posted)).all()
    for comment_date, count in comments_per_day:
        if isinstance(comment_date, date):
            average_comments_data['labels'].append(comment_date.strftime('%Y-%m-%d'))
        else:
            average_comments_data['labels'].append(str(comment_date))
        average_comments_data['data'].append(count)

    # Prepare data for average rating by type chart
    average_rating_by_type_data = {
        'labels': ['Product', 'Service'],
        'data': []
    }
    average_product_rating = db.session.query(db.func.avg(Comment.rating)).join(Product, Comment.product_id == Product.id).scalar()
    average_service_rating = db.session.query(db.func.avg(Comment.rating)).join(Service, Comment.service_id == Service.id).scalar()
    average_rating_by_type_data['data'].append(average_product_rating or 0)
    average_rating_by_type_data['data'].append(average_service_rating or 0)

    # Prepare data for average comments by type chart
    average_comments_by_type_data = {
        'labels': ['Product', 'Service'],
        'data': []
    }
    average_product_comments = db.session.query(db.func.count(Comment.id)).join(Product, Comment.product_id == Product.id).scalar()
    average_service_comments = db.session.query(db.func.count(Comment.id)).join(Service, Comment.service_id == Service.id).scalar()
    average_comments_by_type_data['data'].append(average_product_comments / len(products) if products else 0)
    average_comments_by_type_data['data'].append(average_service_comments / len(services) if services else 0)

    return render_template('dashboard.html', comments=comments_with_items, average_rating_data=json.dumps(average_rating_data), average_comments_data=json.dumps(average_comments_data), average_rating_by_type_data=json.dumps(average_rating_by_type_data), average_comments_by_type_data=json.dumps(average_comments_by_type_data))