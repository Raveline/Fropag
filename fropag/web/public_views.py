"""Web entry point for Fropag."""
# -*- coding: utf-8 -*-
from flask import render_template

from web import app
from model.core import get_publications, get_publication, get_word_data
from model.core import NonExistingDataException


@app.route('/')
def index():
    '''Return the main page.'''
    return render_template('index.html',
                           publications=[p.name for p in get_publications()])

@app.route('/word/<string:word>')
def word_info(word):
    '''Display the word details page.'''
    def prepare_word_page(word_data):
        '''Fill the data we will inject to the template:
        - Is the word forbidden for all publications ?
        - Only for some of those ?'''
        forbidden_info = "Ce mot est suivi pour toutes les publications."
        forbidden_pubs = [p['name'] for p in word_data['publications']
                          if p['forbidden']]
        if word_data['forbidden_all']:
            forbidden_info = "Pour des raisons techniques, nous ne comptons\
            normalement jamais ce mot. Voici toutefois son historique."
        elif len(forbidden_pubs) > 0:
            forbidden_info = "Pour des raisons techniques, ce mot n'est pas\
            suivi pour les publications suivantes : "
            forbidden_info += ','.join(word_data['publications'])
        return render_template('word.html',
                               word=word,
                               forbidden_info=forbidden_info)
    try:
        word_data = get_word_data(word)
        return prepare_word_page(word_data)
    except NonExistingDataException:
        # Let's try with capitalizing / uncapitalizing it
        try:
            if word[0].islower():
                word = word.capitalize()
            else:
                word = word.lower()
            word_data = get_word_data(word)
            return prepare_word_page(word_data)
        except NonExistingDataException:
            return render_template('word.html')

@app.route('/about')
def about():
    '''Return the static about page.'''
    return render_template('about.html')

@app.route('/publication/<string:name>')
def view_publication(name):
    '''Return the details on publication page.'''
    try:
        pub = get_publication(name)
        return render_template('publication.html', publication=pub)
    except NonExistingDataException:
        return render_template('page_not_found.html'), 404
