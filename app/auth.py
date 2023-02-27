import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import text, exc


from app.db import db, get_db_con
from app.rating.rating import init_user_rating

auth = Blueprint('auth', __name__, url_prefix='/auth')


@auth.route('/register', methods=('GET', 'POST'))
def register():
    """ View function for register page """
    if request.method == 'POST':

        # Access form responses
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']

        # Error handling for register
        error = None
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not first_name:
            error = 'First name is required.'

        db_con = get_db_con()
        if error is None:
            try:
                # Insert into d_user
                user_id = db_con.execute(
                    text(f"""
                    INSERT INTO d_user (username, password, first_name) 
                    VALUES ('{username}', '{generate_password_hash(password)}', '{first_name}')
                    RETURNING id;
                    """)
                ).fetchone().id
                db_con.commit()

            except exc.IntegrityError:
                error = f"User {username} is already registered."

            else:
                # Insert into d_ranking with default user
                init_skill, init_uncertainty = init_user_rating()

                # Insert into the d_skill with initialized TrueSkill rating
                db_con.execute(
                    text(
                        f"""
                    INSERT INTO d_skill (user_id, skill, uncertainty) 
                    VALUES ({user_id}, {init_skill}, {init_uncertainty});""")
                )
                db_con.commit()

                # Directly logs in
                session.clear()
                session['user_id'] = user_id
                return redirect(url_for('index'))

        flash(error)

    else:
        if 'user_id' in session:
            return redirect(url_for('rank.index'))

        return render_template('auth/register.html')


@auth.route('/login', methods=('GET', 'POST'))
def login():
    """ View function for login page """
    if request.method == 'POST':

        # Access form responses
        username = request.form['username']
        password = request.form['password']

        # Error handling for login
        db_con = get_db_con()
        error = None
        user = db_con.execute(
            text(f"SELECT * FROM d_user WHERE username = '{username}'")
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user.password, password):
            error = 'Incorrect password.'

        if error is None:
            # session is a dict that stores data across requests. When validation succeeds,
            # the user’s id is stored in a new session. The data is stored in a cookie that is
            # sent to the browser, and the browser then sends it back with subsequent requests.
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('index'))

        flash(error)

    else:
        if 'user_id' in session:
            return redirect(url_for('rank.index'))

        return render_template('auth/login.html')


@auth.before_app_request  # registers a function that runs before the view function, no matter what URL is requested.
def load_logged_in_user():
    user_id = session.get('user_id')
    db_con = get_db_con()

    if user_id is None:
        g.user = None
    else:
        with db_con as con:
            g.user = con.execute(
                text(f'SELECT * FROM d_user WHERE id = {user_id}')
            ).fetchone()


@auth.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


# Decorator definition for views
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        # Redirects if not logged in
        if g.user is None:
            return redirect(url_for('auth.login'))

        # Simply returns the view if logged in
        return view(**kwargs)

    return wrapped_view
