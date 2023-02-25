from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db
from app.rating.rating import update_rating


rank = Blueprint('rank', __name__)


@rank.route('/', methods=['GET'])
@login_required
def index():
    # index page is the ranking
    db = get_db()
    ranking = db.execute(
        """
        SELECT du.id as user_id, du.username as name, ds.skill as skill, ds.uncertainty as uncertainty 
        FROM d_skill ds 
        JOIN d_user du 
            ON ds.user_id = du.id 
        ORDER BY skill DESC;
        """
    ).fetchall()
    return render_template('rank/index.html', ranking=ranking)


@rank.route('/update', methods=['GET', 'POST'])
@login_required
def update():
    """ View for Add Score page """

    if request.method == 'POST':

        # Access form response
        opp_username = request.form['opponent']
        self_score = request.form['your-score']
        opp_score = request.form['opponent-score']

        # Error handling
        db = get_db()
        error = None
        usernames = [row["username"] for row in db.execute('SELECT username FROM d_user').fetchall()]
        if not opp_username or not self_score or not opp_score:
            error = 'All entries must be filled.'
        elif opp_username not in usernames:
            error = 'Opponent\'s username does not exist.'
        elif opp_username == g.user['username']:
            error = 'Opponent cannot be yourself.'
        elif not self_score.isdigit() or not opp_score.isdigit():
            error = "Your/Opponent score must be an integer."
        elif self_score == opp_score:
            error = "Game result cannot be a draw."

        # Query their id, current skill, current uncertainty
        if error is None:

            self_score, opp_score = int(self_score), int(opp_score)

            self_ = db.execute(
                """
                SELECT du.id as user_id, ds.skill as skill, ds.uncertainty as uncertainty
                FROM d_user as du
                JOIN d_skill ds on du.id = ds.id
                WHERE du.id = ?
                """,
                (g.user["id"],)
            ).fetchone()

            opp_ = db.execute(
                """
                SELECT du.id as user_id, ds.skill as skill, ds.uncertainty as uncertainty
                FROM d_user as du
                JOIN d_skill ds on du.id = ds.id
                WHERE du.username = ?
                """,
                (opp_username,)
            ).fetchone()

            # Update their Rating (skill and uncertainty)
            self_id, self_mu, self_sigma = self_["user_id"], self_["skill"], self_["uncertainty"]
            opp_id, opp_mu, opp_sigma = opp_["user_id"], opp_["skill"], opp_["uncertainty"]

            new_self_mu, new_self_sigma, new_opp_mu, new_opp_sigma = update_rating(
                self_mu, self_sigma, self_score, opp_mu, opp_sigma, opp_score)
            # Update d_skill
            db.execute(
                """
                UPDATE d_skill
                SET skill = ?, uncertainty = ?
                WHERE user_id = ?
                """,
                (new_self_mu, new_self_sigma, self_id),
            )
            db.commit()

            db.execute(
                """
                UPDATE d_skill
                SET skill = ?, uncertainty = ?
                WHERE user_id = ?
                """,
                (new_opp_mu, new_opp_sigma, opp_id),
            )
            db.commit()

            # Update d_match
            match = db.execute(
                """
                INSERT INTO d_match(self_user_id, opponent_user_id)
                VALUES (?, ?)
                RETURNING id;
                """,
                (self_id, opp_id),
            ).fetchone()
            db.commit()

            # Update d_score
            db.execute(
                """
                INSERT INTO d_score(match_id, user_id, score, is_winner)
                VALUES (?, ?, ?, ?), (?, ?, ?, ?)
                """,
                (match['id'], self_id, self_score, 1 if self_score > opp_score else 0,
                 match['id'], opp_id, opp_score, 1 if opp_score > self_score else 0),
            )
            db.commit()

            return redirect(url_for('index'))

        flash(error)

    # Else if request method is GET
    return render_template('rank/update.html')


@rank.route('/profile/<int:user_id>', methods=['GET'])
@login_required
def profile(user_id):

    db = get_db()

    games_played = db.execute(
        """
        SELECT du.username as username, COUNT(*) as count
        FROM d_score ds
        JOIN d_user du ON du.id = ds.user_id
        WHERE
        user_id = ?;
        """,
        (user_id,)
    ).fetchone()
    username, count = games_played['username'], games_played['count']

    history = db.execute(
        """
        SELECT is_winner, COUNT(is_winner) AS count
        FROM d_score
        WHERE user_id = ?
        GROUP BY is_winner;
        """,
        (user_id,)
    ).fetchall()
    lost, won = history[0]["count"], history[1]["count"]
    return render_template('rank/profile.html', user_id=user_id, username=username, games_played=count, lost=lost, won=won)
