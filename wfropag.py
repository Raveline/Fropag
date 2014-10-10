# -*- coding: utf-8 -*-
import os
from flask import Flask, render_template, request, session, redirect, url_for
from flask.ext.assets import Environment, Bundle
from flask.json import jsonify
from database import db_session
from functools import wraps
import config

from core import get_publications, get_publication_tops, get_all_tops
from core import delete_publication, modify_publication, follow_publication
from core import get_word_data, boot_sql_alchemy, NonExistingDataException
from core import modify_word, get_publication_frequency

app = Flask(__name__)
app.secret_key = config.SECRET_KEY
app.debug = True
boot_sql_alchemy()

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
# UTILS
#------------------------------
def add_prelude(data):
    data['propers'] = propers_prelude + data['propers'];
    data['commons'] = commons_prelude + data['commons'];

def prelude_stat_dictionary(stats):
    for publication, data in stats.items():
        add_prelude(data)

# CONSTANTS
#------------------------------
propers_prelude = [("Noms propres", "Décompte")]
commons_prelude = [("Noms communs", "Décompte")]

def login_required(f):
    """Make sure the user is logged in. If not, redirct him to the login page."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

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
    return render_template('index.html'
        , publications = [p.name for p in get_publications()])

@app.route('/top_words_all/')
def get_top_words_all():
    p = get_all_tops()
    add_prelude(p)
    return jsonify(p)

@app.route('/top_words_for/')
def get_top_words_for():
    names = request.args.getlist("names[]")
    p = get_publication_frequency(names)
    prelude_stat_dictionary(p)
    return jsonify(p)

@app.route('/admin/word/<string:word>')
def admin_word(word):
    try:
        word_data = get_word_data(word)
        return render_template('admin_word.html',
            w = word_data['word'],
            publications = word_data['publications'],
            forbidden_all = word_data['forbidden_all'])
    except NonExistingDataException:
        return "The word " + word + " does not exist."

@app.route('/admin/publications')
@login_required
def admin_publications():
    return render_template('admin_publications.html', 
                        publications = get_publications())

@app.route('/publication/<int:p_id>')
@login_required
def remove_publication(p_id):
    delete_publication(p_id)
    return redirect(url_for('admin_publications'))
    
@app.route('/publication/add', methods=['POST'])
def add_publication():
    follow_publication(request.form['name']
                    , request.form['url']
                    , request.form['start']
                    , request.form['end'])
    return redirect(url_for('admin_publications'))

@app.route('/publication/update', methods=['POST'])
def update_publication():
    name = request.form['name']
    url = request.form['url']
    begin = request.form['start']
    end = request.form['end']
    idp = request.form['id']
    modify_publication(idp, name, url, begin, end)
    return redirect(url_for('admin_publications'))

@app.route('/word/update', methods=['POST'])
def update_word():
    id_w = request.form['word_id']
    proper = 'proper' in request.form.keys()
    forbidden_all = 'forbidden_all' in request.form.keys()
    forbidden_pubs = request.form.getlist('forbidden_publications')
    modify_word(id_w, proper, forbidden_all, forbidden_pubs)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run()

@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

