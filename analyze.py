from nltk.corpus import PlaintextCorpusReader
from nltk import Text
from nltk.tag.stanford import POSTagger
from publication import Publication, path_to_corpus

posTagger = POSTagger('stanford-tagger/french.tagger'
              ,'stanford-tagger/stanford-postagger.jar'
              ,encoding='utf-8')

def read_corpus_for(publication_folder):
    root = path_to_corpus + publication_folder
    return PlaintextCorpusReader(root, '.*', encoding='utf-8')

def corpus_to_text(corpus):
    return Text(corpus.words())

def get_text_for(publication_folder):
    return corpus_to_text(read_corpus_for(publication_folder))

def tag_text(text):
    return posTagger.tag(text.tokens)   
