# -*- coding: utf-8 -*-
"""This module offers some analysis of studied corpus.
It extracts meaningful words (separating common and proper nouns)
to give statistics on word usage.
stat_from_corpus will give :
- The lexical variety
- The list of common words, without some "banned" words for each
publication (thinks like "share", "read more", etc.)
- TODO The list of proper nouns. (Waiting for Stanford to release that)

Only verbs, adjective and nouns should be left once NLTK
has done its analyzis. The current version is only thought
for french publication, so further work should be done to
adapt it to other languages.
It heavily depends on taggers to perform its analyzis.
Fropag uses the Stanford libraries for those tasks, and
the stanford directory should contains the dependencies
for this task."""

from nltk.corpus import PlaintextCorpusReader
from nltk import Text, word_tokenize
from nltk.tag.stanford import POSTagger
from publication import Publication
from collections import Counter


# Please note : these are the french categories.
# To remove english tags, you'll need to add the proper
# tags.
postagging_to_remove = ['PUNC','DET', 'P', 'C', 'CC'
                       , 'PRO', 'CLS', 'PROREL', 'CS']
proper_nouns = 'NPP'

def tag_text(text):
    """Analyze a text to be able to identify unwanted words."""
    posTagger = POSTagger('stanford/french.tagger'
                        ,'stanford/stanford-postagger.jar'
                        ,encoding='utf-8')
    return posTagger.tag(text.tokens)   

def trim_unwanted_tags(tagged):
    """Remove any words corresponding to tags we do not want
    to analyze."""
    # unfortunately, the posttagger does not always work
    # as it should, and will miss some punctuation.
    # So we'll also trim any non alphanum characters here.
    # Finally, some lone characters can also be identified
    # as foreign words. Let's get rid of those.
    return [w for w in tagged if w[1] not in postagging_to_remove
            and w[0].isalnum() and len(w[0]) > 2]

def get_lexical_richness(words):
    return len(set(words)) / len(words)

def frontpage_to_text(text):
    tokens = word_tokenize(text)
    return Text(tokens)

def get_stats(text):
    nltk_text = frontpage_to_text(text)
    tagged = tag_text(nltk_text)
    filtered = trim_unwanted_tags(tagged)
    proper = [w[0].capitalize() for w in filtered if w[1] == proper_nouns]
    others = [w[0].lower() for w in filtered if w[1] != proper_nouns]
    return (to_counter(proper), to_counter(others)
           ,get_lexical_richness(proper))

def to_counter(words):
    return Counter(words)

if __name__ == "__main__":
    print(get_stats("lefigaro"))
