from app import app

@app.route('/')
def home():
    return "Bienvenue sur mon application Flask !"
