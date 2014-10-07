# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template
from flask.ext.assets import Environment, Bundle
from flask.json import jsonify

from core import get_publications, get_publication_tops

app = Flask(__name__)
app.debug = True
# ASSETS
assets = Environment(app)
assets.load_path = [os.path.join(os.path.dirname(__file__), 'bower_components')]

assets.register(
    'css_all',
    Bundle(
        'bootstrap/dist/css/bootstrap.min.css',
        output="css_all.css"
    )
)

@app.route('/')
def index():
    p = get_publications()
    return render_template('index.html', publications = p)

@app.route('/top_commons/<string:pub_name>')
def get_commons(pub_name):
    p = see_words_for(pub_name)
    return jsonify(p)

if __name__ == "__main__":
    app.run()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
