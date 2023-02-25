from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
import trueskill

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
        SELECT du.username as name, ds.skill as skill, ds.uncertainty as uncertainty 
        FROM d_skill ds JOIN d_user du ON ds.user_id = du.id 
        ORDER BY skill, uncertainty DESC;
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

        db = get_db()
        error = None
        usernames = [row["username"] for row in db.execute('SELECT username FROM d_user').fetchall()]
        if not opp_username or not self_score or not opp_score:
            error = 'All entries must be filled.'
        elif opp_username not in usernames:
            error = 'Opponent\'s username does not exist.'
        elif not self_score.isdigit() or not opp_score.isdigit():
            error = "Your/Opponent score must be an integer."
        elif self_score == opp_score:
            error = "Game result cannot be a draw."

        # Query their id, current skill, current uncertainty
        if error is None:
            self_ = db.execute(
                """
                SELECT du.id as user_id, ds.skill, ds.uncertainty
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

            self_mu, self_sigma, opp_mu, opp_sigma = update_rating(
                self_mu, self_sigma, self_score, opp_mu, opp_sigma, opp_score)

            # Update database
            db.execute(
                """
                UPDATE d_skill
                SET skill = ?, uncertainty = ?
                WHERE user_id = ?
                """,
                (self_mu, self_sigma, self_id),
            )
            db.commit()

            db.execute(
                """
                UPDATE d_skill
                SET skill = ?, uncertainty = ?
                WHERE user_id = ?
                """,
                (opp_mu, opp_sigma, opp_id),
            )
            db.commit()
            return redirect(url_for('index'))

        flash(error)

    # Else if request method is GET
    return render_template('rank/update.html')


@rank.route('/profile', methods=['GET'])
@login_required
def profile():
    return