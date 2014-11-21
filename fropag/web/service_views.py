'''Various services exposed that return JSON.
Used to build the charts on the website.

For documentation purpose, here are the expected
structure.

Answer type
{ 'success' : Boolean,
  'data' : DataStruct }

DataStruct can be : - PropersCommonsSeparated
                    - PublicationSeparated
                    - DataSet

PublicationSeparated type
{ 'publication1' : DataStruct,
  'publication2' : DataStruct,
  etc. }

PropersCommonsSeparated type
{ 'commons' : DataSet,
  'propers' : DataSet }

DataSet type
{ 'title' : String
  'data' : [legend_row, data_rows] }
'''

from flask import request
from flask.json import jsonify

from web import app
from model.core import get_all_tops, get_history_for
from model.core import get_publication_frequency, get_publication_most_used

# CONSTANTS
#------------------------------
propers_prelude = [("Noms propres", "Décompte")]
commons_prelude = [("Noms communs", "Décompte")]
TOP_10_ALL_PROPERS_TITLE = "10 premières fréquences des noms propres pour toutes les publications suivies."
TOP_10_ALL_COMMONS_TITLE = "10 premières fréquences des autres types de mots pour toutes les publications suivies."
PRELUDE_COMMONS_TITLE = "Les {} premiers mots courants les plus fréquents de {}"
PRELUDE_PROPERS_TITLE = "Les {} premiers noms propres les plus fréquents de {}"


# UTILS
#------------------------------
def add_prelude(data):
    '''Add a legend to a dictionary composed of lists of words,
    'propers' and 'commons'.'''
    data['propers'] = propers_prelude + data['propers']
    data['commons'] = commons_prelude + data['commons']


def prelude_stat_dictionary(stats, number_of_items):
    '''Stats being a dictionary of dictionary like this one :
    { 'newspaper1' : { 'propers' : [...], 'commons': [...] },
    add to each of the subdictionary a prelude giving a header
    to the data. This should be internationalized later.'''
    new_dict = {}
    for publication, data in stats.items():
        add_prelude(data)
        new_dict[publication] = {'propers':
                                 {'title': PRELUDE_PROPERS_TITLE.
                                  format(number_of_items,
                                         publication),
                                  'data': data['propers']},
                                 'commons':
                                 {'title': PRELUDE_COMMONS_TITLE.
                                  format(number_of_items,
                                         publication),
                                  'data': data['commons']}}
    return new_dict


def separated_to_data_set(data, title_commons, title_propers):
    '''Given a dict with propers, commons, mindate, maxdate,
    make it into a nice dataset with the proper structure
    and the given titles.'''
    return {'commons':
            {'title': title_commons,
             'data': data['commons']},
            'propers':
                {'title': title_propers,
                 'data': data['propers']},
            'mindate': data['mindate'],
            'maxdate': data['maxdate']}


def to_successful_answer(data_set):
    '''Given any of our DataStruct, make it in into the
    Answer type and jsonify it.'''
    return jsonify({'success': True,
                    'data': data_set})

# ROUTES
#------------------------------
@app.route('/top_words_all/')
def get_top_words_all():
    '''Return a JSON with the top 10 common words and top 10 proper
    words for all publication combined.'''
    top10 = get_all_tops()
    add_prelude(top10)
    data_set = separated_to_data_set(top10,
                                     TOP_10_ALL_COMMONS_TITLE,
                                     TOP_10_ALL_PROPERS_TITLE)
    return to_successful_answer(data_set)

@app.route('/word/history/<string:word>')
def get_history_for_word(word):
    '''Return the usage history of the word received in parameter.
    Result is a JSON with the structure :
    [date, newspaper1, newspaper2, ...]'''
    info = get_history_for(word)
    title = "Historique d'utilisation du mot {}.".format(word)
    data_set = {'title': title, 'data': info}
    return to_successful_answer(data)

@app.route('/top_words_for/')
def get_top_words_for():
    '''Return the top words for a list of publications passed
    as an array in GET parameter. Result is a json dictionnary.'''
    names = request.args.getlist("names[]")
    top_words_dict = get_publication_frequency(names)
    new_dict = prelude_stat_dictionary(top_words_dict, 10)
    return to_successful_answer(new_dict)

@app.route('/publication/frequency/<string:publication>')
def most_used_words_of(publication):
    '''Return the 100th most used common words
    and the 100th most used proper words, as a dictionary.'''
    top100 = get_publication_most_used(publication)
    add_prelude(top100)
    data_set = separated_to_data_set(top100,
                                     PRELUDE_COMMONS_TITLE.format(100,
                                                                  publication),
                                     PRELUDE_PROPERS_TITLE.format(100,
                                                                  publication))
    return to_successful_answer(data_set)
