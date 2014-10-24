'''Various services exposed that return JSON.
Used to build the charts on the website.'''
from flask import request
from flask.json import jsonify

from web import app
from model.core import get_all_tops, get_history_for
from model.core import get_publication_frequency, get_publication_most_used

# CONSTANTS
#------------------------------
propers_prelude = [("Noms propres", "Décompte")]
commons_prelude = [("Noms communs", "Décompte")]

# UTILS
#------------------------------
def add_prelude(data):
    '''Add a legend to a dictionary composed of lists of words,
    'propers' and 'commons'.'''
    data['propers'] = propers_prelude + data['propers']
    data['commons'] = commons_prelude + data['commons']

def prelude_stat_dictionary(stats):
    '''Stats being a dictionary of dictionary like this one :
    { 'newspaper1' : { 'propers' : [...], 'commons': [...] },
    add to each of the subdictionary a prelude giving a header
    to the data. This should be internationalized later.'''
    for publication, data in stats.items():
        add_prelude(data)

# ROUTES
#------------------------------
@app.route('/top_words_all/')
def get_top_words_all():
    '''Return a JSON with the top 10 common words and top 10 proper
    words for all publication combined.'''
    top10 = get_all_tops()
    add_prelude(top10)
    return jsonify(top10)

@app.route('/word/history/<string:word>')
def get_history_for_word(word):
    '''Return the usage history of the word received in parameter.
    Result is a JSON with the structure :
    [date, newspaper1, newspaper2, ...]'''
    info = get_history_for(word)
    return jsonify({'success': True, 'data' : info})

@app.route('/top_words_for/')
def get_top_words_for():
    '''Return the top words for a list of publications passed
    as an array in GET parameter. Result is a json dictionnary.'''
    names = request.args.getlist("names[]")
    top_words_dict = get_publication_frequency(names)
    prelude_stat_dictionary(top_words_dict)
    return jsonify(top_words_dict)

@app.route('/publication/frequency/<string:publication>')
def most_used_words_of(publication):
    '''Return the 100th most used common words
    and the 100th most used proper words, as a dictionary.'''
    result = get_publication_most_used(publication)
    add_prelude(result)
    return jsonify(result)
