'''This module handle the process of reading and
analyzing front pages.'''
import time
import multiprocessing
import logging

from publication import Publication, Word, FrontPage, WordCount
from database import db_session, get_engine

from reader import read_front_page, UnreadablePageException
from analyze import get_stats, EmptyContentException

_log = logging.getLogger('fropag.read')

def read():
    """Read every frontpages followed.
    Get the followed publications from the database,
    then read them. This being a lengthy process, we'll
    try and multiprocess it to see if it helps."""
    time0 = time.time()
    publications = db_session.query(Publication).all()
    processes = []
    results = multiprocessing.Queue()
    logs = multiprocessing.Queue()
    for pub in publications:
        processes.append(multiprocessing.Process(target=read_and_analyze,
                                                 args=(pub, results,logs,)))
    [p.start() for p in processes]
    [p.join() for p in processes]
    # Print all collected log
    while not logs.empty():
        record = logs.get()
        _log.handle(record)

    _log.info("Finished reading.")
    save_all(results)
    return "Read and analyzed {} front pages in {} secs.".\
           format(len(publications), str(time.time() - time0))

def read_and_analyze(publication, queue, log_queue):
    """Read a frontpage using the reader module.
    Put the result in a queue."""
    def prepare_log():
        h = logging.handlers.QueueHandler(log_queue)
        sublog = logging.getLogger('fropag.readsub')
        sublog.addHandler(h)
        sublog.setLevel(logging.INFO)
        return sublog
    sublog = prepare_log()
    sublog.info("Reading frontpage for %s at %s", publication.name,
                 publication.url)
    try:
        page = read_front_page(publication.url)
        stats = get_stats(page)
        queue.put((publication, stats))
        sublog.info('Finished reading %s', publication.name)
    except UnreadablePageException as exception:
        sublog.error('%s cannot be read.', publication.name)
        return
    except EmptyContentException:
        _log.error('No content for %s.', publication.name)
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

def save_all(q):
    while not q.empty():
        pair = q.get()
        # This will get us a pair (Publication, (Stats))
        publication = pair[0]
        _log.info('Saving information for %s', publication.name)
        stats = pair[1]
        new_front_page = FrontPage(publication_id = publication.id
                              ,lexical_richness = stats[2])
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
        logging.debug("Adding word %s", w)
        db_session.begin()
        db_session.add(new_word)
        db_session.commit()
        return new_word.id
