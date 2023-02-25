from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort
import trueskill

from app.auth import login_required
from app.db import get_db


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
    # add score page
    if request.method == 'POST':
        opponent = request.form['opponent']
        your_score = request.form['your-score']
        opponent_score = request.form['opponent-score']
        db = get_db()

    # Else if request method is GET
    return render_template('rank/update.html')




@rank.route('/profile', methods=['GET'])
@login_required
def profile():
    return