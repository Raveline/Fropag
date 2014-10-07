# -*- coding: utf-8 -*-
import multiprocessing
import time
from sqlalchemy import func, desc
from database import Base, engine, db_session
from publication import Publication, Word, FrontPage, WordCount

from reader import read_front_page
from analyze import get_stats

propers_prelude = [("Noms propres", "Décompte")]
commons_prelude = [("Noms communs", "Décompte")]

def separate_propers_and_commons(query):
    results = {}
    propers = query.filter(Word.proper == True).all()[:10]
    commons = query.filter(Word.proper == False).all()[:10]
    results['propers'] = propers_prelude + propers;
    results['commons'] = commons_prelude + commons;
    return results

def get_all_tops():
    return separate_propers_and_commons(word_counting_query())

def get_publications():
    return [str(p[0]) for p in db_session.query(Publication.name).all()]

def get_publication_tops(names):
    # This is rather ugly. But getting limited result for grouped queries
    # is rather impracticable. Best solution will be to cache this result.
    results = {}
    for (p_id, p_name) in db_session.query(Publication.id, Publication.name).\
                        filter(Publication.name.in_(names)):
        q = word_counting_query().filter(Publication.id == p_id)
        results[p_name] = separate_propers_and_commons(q)
    return results

def join_from_words_to_publication(q):
    return q.join(WordCount, Word.id == WordCount.word_id).\
      join(FrontPage, WordCount.frontpage_id == FrontPage.id).\
      join(Publication, Publication.id == FrontPage.publication_id)

def word_counting_query():
    q = db_session.query(Word.word, func.sum(WordCount.count).label('sumcount'))
    q = join_from_words_to_publication(q)
    return q.group_by(Word.word).order_by(desc('sumcount'))

def see_words_for(publication_name, proper, limit = 10):
    q = word_counting_query().filter(Publication.name == publication_name).\
            filter(Word.proper == proper).\
            all()[:limit]
    return q

def follow_publication(name, url, start, end):
    new_publication = Publication(name=name, url=url
                        , start=start, end=end)
    db_session.add(new_publication)
    db_session.commit()
    return "Following publication {} at {} ".format(name, url)

def save_all(q):
    while not q.empty():
        pair = q.get()
        # This will get us a pair (Publication, (Stats))
        publication = pair[0]
        stats = pair[1]
        new_front_page = FrontPage(publication_id = publication.id
                              ,lexical_richness = stats[2])
        db_session.add(new_front_page)
        db_session.commit()
        save_words(new_front_page.id, stats[0], stats[1])

def save_words(publication_id, propers, commons):
        # Get id for words - this is going to be slow - particularly for new words
        # but session cache-like abilities could help us
        proper_nouns = [(get_word_id(w[0], True), w[1]) for w in propers.items()]
        common_nouns = [(get_word_id(w[0], False), w[1]) for w in commons.items()]

        # This being bulk inserts, we're going to use SqlAlchemy Core
        engine.execute(
            WordCount.__table__.insert(),
            [{'count' : w[1], 'frontpage_id' : publication_id
            ,'word_id' : w[0]} for w in common_nouns])
        engine.execute(
            WordCount.__table__.insert(),
            [{'count' : w[1], 'frontpage_id' : publication_id
            ,'word_id' : w[0]} for w in proper_nouns])

def analyze_process():
    """Read every frontpages followed.
    Get the followed publications from the database,
    then read them. This being a lengthy process, we'll
    try and multiprocess it to see if it helps."""
    t0 = time.time()
    publications = db_session.query(Publication).all()
    processes = []
    results = multiprocessing.Queue()
    for pub in publications:
        processes.append(multiprocessing.Process(target=read_and_analyze, args=(pub, results,)))
    [p.start() for p in processes]
    [p.join() for p in processes]
    save_all(results)
    return "Read and analyzed {} front pages in {} secs.".format(len(publications), str(time.time() - t0))

def read_and_analyze(publication, q):
    page = read_front_page(publication.url, publication.start, publication.end)
    stats = get_stats(page)
    q.put((publication, stats))

def delete_front_page(fp_id):
    """Delete ONE front page from the database.
    Must delete the dependent wordcounts."""
    found = db_session.query(FrontPage).filter_by(id=fp_id).one()
    if found:
        db_session.delete(found)
        db_session.commit()
        return "Deleted."
    else:
        "No such frontpage."

def get_word_id(w, p):
    """Get the id of w in the database.
    If w doesn't exist, insert it and give return its id."""
    found = db_session.query(Word).filter_by(word = w, proper = p).first()
    if found:
        return found.id
    else:
        new_word = Word(word = w, proper = p)
        db_session.add(new_word)
        db_session.commit()
        return new_word.id

def init_db():
    Base.metadata.create_all(engine)
    return "Created database."
