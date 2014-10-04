from nltk.corpus import PlaintextCorpusReader
from publication import Publication, path_to_corpus

def read_corpus_for(publication_folder):
    root = path_to_corpus + publication_folder
    return PlaintextCorpusReader(root, '.*')
