# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, request, session, redirect, url_for
from flask.ext.assets import Environment, Bundle
from flask.json import jsonify
from database import db_session
import config

from core import get_publications, get_publication_tops, get_all_tops

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
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
assets.register(
    'js_all',
    Bundle(
        'jquery/dist/jquery.min.js',
        'bootstrap/dist/js/bootstrap.min.js'
    )
)

@app.route('/admin')
def connect():
    return render_template('connect.html')

@app.route('/login', methods = ['POST'])
def login():
    login = request.form['login']
    password = request.form['password']
    if login == config.LOGIN and password == config.PASSWORD:
        session['admin'] = True
        return redirect(url_for('index'))
    else:
        session['admin'] = False
        return redirect(url_for('connect'))

@app.route('/')
def index():
    p = get_publications()
    return render_template('index.html', publications = p)

@app.route('/top_words_all/')
def get_top_words_all():
    p = get_all_tops()
    return jsonify(p)

@app.route('/top_words_for/')
def get_top_words_for():
    names = request.args.getlist("names[]")
    p = get_publication_tops(names)
    return jsonify(p)

if __name__ == "__main__":
    app.run()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()
