'''This module handle the process of reading and
analyzing front pages.'''
import time
import multiprocessing
import logging

from model.publication import Publication, Word, FrontPage, WordCount
from database import db_session, get_engine

from process.reader import read_front_page, UnreadablePageException
from process.analyze import get_stats, EmptyContentException

_log = logging.getLogger('fropag.read')

def read_only(pubs):
    '''Read only a list of publications.'''
    _log.info("Reading only " + ','.join(pubs))
    publications = db_session.query(Publication).\
                    filter(Publication.name.in_(pubs)).all()
    return read(publications)

def read_every():
    '''Read every publications.'''
    _log.info("Reading every publications.")
    publications = db_session.query(Publication).all()
    return read(publications)

def read(publications):
    '''Read the publications received as parameter.
    This being a lengthy process, we'll try and multiprocess 
    it to improve its efficiency.'''
    time0 = time.time()
    processes = []
    results = []
    manager = multiprocessing.Manager()
    results = manager.list()
    logs = manager.list()
    for pub in publications:
        processes.append(multiprocessing.Process(target=read_and_analyze,
                                                 args=(pub, results, logs,)))
    [p.start() for p in processes]
    [p.join() for p in processes]

    for error in logs:
        _log.error(error)

    _log.info("Finished reading.")
    save_all(results)
    return "Read and analyzed {} front pages in {} secs.".\
           format(len(publications), str(time.time() - time0))


def read_and_analyze(publication, results, error_log):
    '''Read a frontpage using the reader module.
    Put the result in a queue.'''
    try:
        page = read_front_page(publication.url)
        stats = get_stats(page)
        results.append((publication, stats))
    except UnreadablePageException as exception:
        error_log.append('{} cannot be read : {}'.format(publication.name,
                                                         exception))
        return
    except EmptyContentException:
        error_log.append('No content for {}.'.format(publication.name))
        return

def save_words(publication_id, propers, commons):
    # Get id for words - this is going to be slow - particularly for new words
    # but session cache-like abilities could help us
    _log.info('Checking for new words and getting word ids...')
    proper_nouns = [(get_word_id_or_add_it(w[0], True), w[1]) 
                        for w in propers.items()]
    common_nouns = [(get_word_id_or_add_it(w[0], False), w[1]) 
                        for w in commons.items()]
    _log.info('Done.')

    engine = get_engine()
    # This being bulk inserts, we're going to use SqlAlchemy Core
    if common_nouns:
        engine.execute(
            WordCount.__table__.insert(),
            [{'count' : w[1], 'frontpage_id' : publication_id,
              'word_id' : w[0]} for w in common_nouns])
    _log.info('Added common words.')
    if proper_nouns:
        engine.execute(
            WordCount.__table__.insert(),
            [{'count' : w[1], 'frontpage_id' : publication_id,
              'word_id' : w[0]} for w in proper_nouns])
    _log.info('Added proper nouns.')

def save_all(publication_and_results):
    '''Take a list of publication object and stats extracted
    from its frontpage and save the result in the database.'''
    for pair in publication_and_results:
        # This will get us a pair (Publication, (Stats))
        publication = pair[0]
        _log.info('Saving information for %s', publication.name)
        stats = pair[1]
        new_front_page = FrontPage(publication_id=publication.id,
                                   lexical_richness=stats[2])
        db_session.begin()
        db_session.add(new_front_page)
        db_session.commit()
        _log.info('Added frontpage.')
        save_words(new_front_page.id, stats[0], stats[1])

def get_word_id_or_add_it(w, p):
    """Get the id of w in the database.
    If w doesn't exist, insert it and give return its id."""
    found = db_session.query(Word).filter_by(word = w, proper = p).first()
    if found:
        return found.id
    else:
        new_word = Word(word = w, proper = p)
        _log.debug("Adding word %s", w)
        db_session.begin()
        db_session.add(new_word)
        db_session.commit()
        return new_word.id
