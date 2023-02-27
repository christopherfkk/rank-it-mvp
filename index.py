from app import create_app
from sqlalchemy import text
from app.db import db
import os


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        with open('app/schema.sql', 'r') as f:
            schema = f.read()
            with db.engine.connect() as conn:
                conn.execute(text(schema))
                conn.commit()

    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
