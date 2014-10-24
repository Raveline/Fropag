'''Administration access.'''
from functools import wraps
from flask import render_template, request, session, redirect, url_for

import config
from web import app
from model.core import get_word_data, NonExistingDataException
from model.core import get_publications, follow_publication
from model.core import delete_publication, modify_publication
from model.core import modify_word

def login_required(fun):
    """Make sure the user is logged in.
    If not, redirect him to the login page."""
    @wraps(fun)
    def decorated_function(*args, **kwargs):
        '''Redirect to index if not in an admin session.'''
        if not session.get('admin'):
            return redirect(url_for('index'))
        return fun(*args, **kwargs)
    return decorated_function

@app.route('/admin')
def connect():
    '''Render the connection form.'''
    return render_template('connect.html')

@app.route('/login', methods=['POST'])
def login():
    '''Try and login the user. Redirect him or her to
    the index page if failed.'''
    user_login = request.form['login']
    user_password = request.form['password']
    if user_login == config.LOGIN\
       and user_password == config.PASSWORD:
        session['admin'] = True
        return redirect(url_for('index'))
    else:
        session['admin'] = False
        return redirect(url_for('connect'))

@app.route('/admin/word/<string:word>')
@login_required
def admin_word(word):
    '''Administration page for a single word.'''
    try:
        word_data = get_word_data(word)
        return render_template('admin_word.html',
                               w=word_data['word'],
                               publications=word_data['publications'],
                               forbidden_all=word_data['forbidden_all'])
    except NonExistingDataException:
        return "The word " + word + " does not exist."

@app.route('/admin/publications')
@login_required
def admin_publications():
    """Access to the publication administration menu."""
    return render_template('admin_publications.html',
                           publications=get_publications())

@app.route('/publication/delete/<int:p_id>')
@login_required
def remove_publication(p_id):
    '''Signal by the administrator that a publication
    must be unfollowed (and thus, deleted from the db).'''
    delete_publication(p_id)
    return redirect(url_for('admin_publications'))

@app.route('/publication/add', methods=['POST'])
@login_required
def add_publication():
    '''Handle a POST request containing information on
    a new publication.
    TODO: add periodicity'''
    follow_publication(request.form['name'],
                       request.form['url'])
    return redirect(url_for('admin_publications'))

@app.route('/publication/update', methods=['POST'])
def update_publication():
    '''Handle A POST request containing information to
    modify a publication.
    TODO : handle periodicity.'''
    name = request.form['name']
    url = request.form['url']
    idp = request.form['id']
    modify_publication(idp, name, url)
    return redirect(url_for('admin_publications'))

@app.route('/word/update', methods=['POST'])
@login_required
def update_word():
    '''Handle a POST request containing information to
    modify a word.'''
    id_w = request.form['word_id']
    proper = 'proper' in request.form.keys()
    forbidden_all = 'forbidden_all' in request.form.keys()
    forbidden_pubs = request.form.getlist('forbidden_publications')
    modify_word(id_w, proper, forbidden_all, forbidden_pubs)
    return redirect(url_for('index'))
