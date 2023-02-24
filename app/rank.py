from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from app.auth import login_required
from app.db import get_db


rank = Blueprint('rank', __name__)


@rank.route('/', methods=['GET'])
@login_required
def index():
    # index page is the ranking

    db = get_db()
    ranking = db.execute(
        'SELECT dr.id as rank, du.username as name'
        ' FROM d_ranking dr JOIN d_user du ON dr.user_id = du.id'
    ).fetchall()
    return render_template('rank/index.html', ranking=ranking)


@rank.route('/update', methods=['GET', 'POST'])
@login_required
def update():
    # add a new score
    if request.method == 'POST':
        return
    return render_template('rank/update.html')


@rank.route('/profile', methods=['GET'])
@login_required
def profile():
    return