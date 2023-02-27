from app import create_app
from sqlalchemy import text
from app.db import db

app = create_app()

with app.app_context():
    with open('app/schema.sql', 'r') as f:
        schema = f.read()
        with db.engine.connect() as conn:
            conn.execute(text(schema))
            conn.commit()

app.run()
