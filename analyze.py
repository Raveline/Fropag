from nltk.corpus import PlaintextCorpusReader
from nltk import Text
from nltk.tag.stanford import POSTagger
from publication import Publication, path_to_corpus
from collections import Counter

posTagger = POSTagger('stanford-tagger/french.tagger'
              ,'stanford-tagger/stanford-postagger.jar'
              ,encoding='utf-8')

# Please note : these are the french categories.
# To remove english tags, you'll need to add the proper
# tags.
postagging_to_remove = ['PUNC','DET', 'P', 'C', 'CC'
                       , 'PRO', 'CLS', 'PROREL', 'CS']

def read_corpus_for(publication_folder):
    root = path_to_corpus + publication_folder
    return PlaintextCorpusReader(root, '.*', encoding='utf-8')

def corpus_to_text(corpus):
    return Text(corpus.words())

def get_text_for(publication_folder):
    return corpus_to_text(read_corpus_for(publication_folder))

def tag_text(text):
    return posTagger.tag(text.tokens)   

def trim_unwanted_tags(tagged):
    # unfortunately, the posttagger does not always work
    # as it should, and will miss some punctuation.
    # So we'll also trim any non alphanum characters here.
    # Finally, some lone characters can also be identified
    # as foreign words. Let's get rid of those.
    return [w[0].lower() for w in tagged if w[1] not in postagging_to_remove
            and w[0].isalnum() and len(w[0]) > 2]

def reduce_to_wanted_words(publication_folder):
    tagged = tag_text(get_text_for(publication_folder))
    filtered = trim_unwanted_tags(tagged)
    return filtered

def get_most_used(words):
    return Counter(words)

if __name__ == "__main__":
    print(get_most_used(reduce_to_wanted_words("lefigaro")))
