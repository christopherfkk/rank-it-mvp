from app import create_app
from db import init_db

app = create_app()
with app.app_context():
    db = init_db()
