import random
from datetime import datetime, timedelta

import bcrypt

from app.models import Comment, Product, Role, Service, User
from app import app, db, bcrypt
from app.utils import predict_comment_rating

NUM_PRODUCTS = 7  # Nombre de produits à générer
NUM_SERVICES = 5  # Nombre de services à générer
MIN_COMMENTS = 5  # Nombre minimum de commentaires à générer pour chaque produit et service
MAX_COMMENTS = 10  # Nombre maximum de commentaires à générer pour chaque produit et service
USER_IDS = [1, 2, 3]  # ID des utilisateurs qui postent les commentaires

# Contenu de base pour les commentaires
COMMENTS_STARTERS = [
    "This", "I think this", "Honestly,", "In my opinion,", "Wow!", "Well,"
]
COMMENTS_MIDDLE = [
    "is amazing.", "could be better.", "exceeded my expectations.", 
    "did not meet my expectations.", "was worth every penny.", 
    "is not worth the price.", "is a must-buy!", "is okay for the price."
]

# Générer des utilisateurs par défaut
DEFAULT_USERS = [
    {"username": "user1", "password": "user1", "role_id": 1},
    {"username": "user2", "password": "user2", "role_id": 1},
    {"username": "user3", "password": "user3", "role_id": 1},
    {"username": "val", "password": "val", "role_id": 2},
    {"username": "kyky", "password": "kyky", "role_id": 2},
    {"username": "ben", "password": "ben", "role_id": 2}
]

# Générer des produits, services et assigner les commentaires aléatoires
with app.app_context():
    db.create_all()

    # Créer les rôles
    user_role = Role(name='User')
    admin_role = Role(name='Admin')
    db.session.add(user_role)
    db.session.add(admin_role)
    db.session.commit()

    # Créer des utilisateurs par défaut
    user_ids = []
    for user_data in DEFAULT_USERS:
        hashed_password = bcrypt.generate_password_hash(user_data["password"]).decode('utf-8')
        user = User(username=user_data["username"], password=hashed_password, role_id=user_data["role_id"])
        db.session.add(user)
        db.session.commit()
        user_ids.append(user.id)

    # Générer des produits
    for i in range(NUM_PRODUCTS):
        product = Product(name=f"Product {i+1}", price=random.randint(10, 100), date_posted=datetime.utcnow())
        db.session.add(product)
        db.session.commit()  # Commit pour obtenir l'ID du produit

        # Générer des commentaires pour le produit
        num_comments = random.randint(MIN_COMMENTS, MAX_COMMENTS)
        for _ in range(num_comments):
            starter = random.choice(COMMENTS_STARTERS)
            middle = random.choice(COMMENTS_MIDDLE)
            content = f"{starter} {middle}"

            rating = predict_comment_rating(content)
            user_id = random.choice(USER_IDS)
            date_posted = datetime.utcnow() - timedelta(days=random.randint(0, 30))
            comment = Comment(
                content=content,
                rating=rating,
                date_posted=date_posted,
                user_id=user_id,
                product_id=product.id
            )
            db.session.add(comment)

    # Générer des services
    for i in range(NUM_SERVICES):
        service = Service(name=f"Service {i+1}", price=random.randint(10, 100), date_posted=datetime.utcnow())
        db.session.add(service)
        db.session.commit()  # Commit pour obtenir l'ID du service

        # Générer des commentaires pour le service
        num_comments = random.randint(MIN_COMMENTS, MAX_COMMENTS)
        for _ in range(num_comments):
            starter = random.choice(COMMENTS_STARTERS)
            middle = random.choice(COMMENTS_MIDDLE)
            content = f"{starter} {middle}"

            rating = predict_comment_rating(content)
            user_id = random.choice(USER_IDS)
            date_posted = datetime.utcnow() - timedelta(days=random.randint(0, 30))
            comment = Comment(
                content=content,
                rating=rating,
                date_posted=date_posted,
                user_id=user_id,
                service_id=service.id
            )
            db.session.add(comment)

    db.session.commit()
    print(f"Generated {NUM_PRODUCTS} products, {NUM_SERVICES} services, and comments for each.")