from app import db
from flask_login import UserMixin

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True)
    password = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    role = db.relationship('Role', backref=db.backref('users', lazy=True))

    def __repr__(self):
        return f'<User {self.username}>'

# Modèle pour les produits
class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    price = db.Column(db.Float, nullable=False)

    # Relation avec les commentaires
    comments = db.relationship('Comment', backref='product', lazy=True)

    def __repr__(self):
        return f'<Product {self.name}>'
    
class Service(db.Model):
    __tablename__ = 'services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"Service('{self.name}', '{self.price}')"

# Modèle pour les commentaires
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)

    # Clés étrangères
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=True)

    def __repr__(self):
        return f'<Comment {self.content[:20]}...>'