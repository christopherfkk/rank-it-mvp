import sqlite3
import click
from flask import current_app, g
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def get_db_con():
    if 'db' not in g:
        g.db_con = db.engine.connect()
    return g.db_con


# def close_db(e=None):
#     db = g.pop('db', None)
#
#     if db is not None:
#         db.close()
#
#
# def init_db():
#     db = get_db_con()
#
#     with current_app.open_resource('./schema.sql') as f:  # opens file relative to "app" package
#         db.executescript(f.read().decode('utf8'))
#
#
# @click.command('init-db')
# def init_db_command():
#     """Clear the existing data and create new tables."""
#     init_db()
#     click.echo('Initialized the database.')
#
#
# # def init_app(app):
# #     # tells Flask to call that function when cleaning up after returning the response
# #     app.teardown_appcontext(close_db)
# #     # adds a new command that can be called with the flask command
# #     app.cli.add_command(init_db_command)
