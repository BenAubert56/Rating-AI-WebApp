# Déploiement de notre application

## Activation du venv
Aller dans le workdir où l'application est stocké. Exécuter la commande pour activer l'environnement virtuel. Workdir du projet : "/Rating-AI-WebApp"
`cd env/Scripts`
`activate`

Revenir au workdir
`cd ../..`

## Installation des packages
`pip install -r requirements.txt`

## Génération de la base de données par défaut
`python generated_bdd.py`

## Lancement de l'application
`python run.py`
Il y aura plusieurs compte par défaut grâce à la génération automatique.
- Pour utiliser un compte avec le rôle "user", utiliser un des comptes suivants ("user1", "user2", "user3"), le mot de passe est le nom du user.
- Pour utiliser un compte avec le rôle "admin", utiliser un des comptes suivants ("val", "kyky", "ben"), le mot de passe est le nom du user.
- Sinon créer un compte directement en cliquant sur "Register" sur la page de connexion.


## Ouvrir l'application
Ouvrir un navigateur et aller sur http://127.0.0.1:8050

## Stoper l'application
Faire un `Ctrl + C` dans le terminal

## Désactiver le venv
`deactivate`

### Fin de la procédure