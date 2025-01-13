from app import app, db
from app.models import Role

with app.app_context():
    db.create_all()

    # Créer les rôles de base
    if not Role.query.filter_by(name='User').first():
        user_role = Role(name='User')
        db.session.add(user_role)

    if not Role.query.filter_by(name='Admin').first():
        admin_role = Role(name='Admin')
        db.session.add(admin_role)

    db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=8081)