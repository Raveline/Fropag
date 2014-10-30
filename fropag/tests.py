import unittest
import datetime
from collections import Counter
import config
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker, scoped_session

from database import *
from model.publication import *
from model.core import *
from process.read_process import save_words

class DBTesting(unittest.TestCase):
    def setUp(self):
        config.DB_USER = "testUser"
        config.DB_PASSWORD = "testPwd"
        config.DB_NAME = "testFropag"
        boot_sql_alchemy()
        Base.metadata.create_all(engine)

    def tearDown(self):
        Base.metadata.drop_all(engine)

class BasicHighLevelFunctions(DBTesting):
    def test_follow_publication(self):
        test_url = "http://test.test"
        test_name = "Test publication"
        follow_publication(test_name, test_url)
        try:
            # The proper publication has been inserted
            q = db_session.query(Publication).filter(Publication.name == test_name).one()
            self.assertEqual(q.url, test_url)
            # Only one publication has been inserted
            self.assertEqual(1, db_session.query(Publication).count())
        except:
            self.fail("Couldn't fetch ONE result for query.")

class DatabaseExtraction(DBTesting):
    def follow_two_publications(self):
        # Insert two publications for every test requiring some publications
        follow_publication("Test1", "")
        follow_publication("Test2", "")
        self.pub1 = db_session.query(Publication).filter(Publication.name == "Test1").one().id
        self.pub2 = db_session.query(Publication).filter(Publication.name == "Test2").one().id

    def create_three_frontpages(self):
        # Add three frontpages for every test requiring them
        # Frontpage 1 and 2 for pub1
        db_session.begin()
        date1 = datetime.datetime(1999, 1, 1, 12,12,12)
        date2 = datetime.datetime(1999, 1, 2, 12,12,12)
        date3 = datetime.datetime(1999, 1, 1, 12,12,12)
        self.nfp1 = FrontPage(publication_id = self.pub1,
                              time_of_publication = date1) 
        self.nfp2 = FrontPage(publication_id = self.pub1,
                              time_of_publication = date2)
        # Frontpage 3 for pub2
        self.nfp3 = FrontPage(publication_id = self.pub2,
                              time_of_publication = date3)
        db_session.add(self.nfp1)
        db_session.add(self.nfp2)
        db_session.add(self.nfp3)
        db_session.commit()

    def add_basic_data(self):
        self.follow_two_publications()
        self.create_three_frontpages()
        proper_counter1 = Counter({'proper1' : 1})
        common_counter1 = Counter({'word1' : 2, 'word2' : 1})
        common_counter2 = Counter({'word1' : 1, 'word3' : 4})
        proper_counter2 = Counter({'proper1' : 1, 'proper2' : 2})
        common_counter3 = Counter({'word1' : 12, 'word4' : 2})
        proper_counter3 = Counter({'proper3' : 2})
        # Serialize those counters...
        save_words(self.nfp1.id, proper_counter1, common_counter1)
        save_words(self.nfp2.id, proper_counter2, common_counter2)
        save_words(self.nfp3.id, proper_counter3, common_counter3)

    def test_get_dates(self):
        '''Bug tracked the 10/17/2014 : dates did not appear
        on the main page.'''
        self.add_basic_data()
        result = get_publication_tops(["Test1", "Test2"])
        test1 = result['Test1']
        test2 = result['Test2']
        self.assertEqual(test1['mindate'], '01/01/1999')
        self.assertEqual(test1['maxdate'], '02/01/1999')
        self.assertEqual(test2['mindate'], '01/01/1999')
        self.assertEqual(test2['maxdate'], '01/01/1999')

    def test_get_words(self):
        self.add_basic_data()
        result = [v[:2] for v in see_words_for("Test1", False)]
        result = dict(result)
        # Are the proper words here ?
        self.assertTrue('word1' in result.keys()
                    , "Every words in this publication should be there")
        self.assertTrue('word2' in result.keys()
                    , "Every words in this publication should be there")
        self.assertTrue('word3' in result.keys()
                    , "Every words in this publication should be there")
        self.assertFalse('word4' in result.keys()
                    , "Only words in this publication should be there")
        # Are they properly counted ?
        self.assertEqual(result['word1'], 3)

    def test_word_data(self):
        self.follow_two_publications()

        db_session.begin()
        w1 = Word(word = "word1", proper = False)
        w2 = Word(word = "word2", proper = True)
        db_session.add(w1)
        db_session.add(w2)
        db_session.commit()

        db_session.begin()
        # Word1 is only forbidden in Publication1
        forbidden1 = Forbidden(word_id = w1.id, publication_id = self.pub1)
        # Word2 is only forbidden everywhere
        forbidden2 = Forbidden(word_id = w2.id)
        db_session.add(forbidden1)
        db_session.add(forbidden2)
        db_session.commit()

        data1 = get_word_data("word1")
        data2 = get_word_data("word2")
        self.assertFalse(data1['forbidden_all'])
        self.assertTrue(data2['forbidden_all'])
        self.assertEqual(data1['word'].word, 'word1')
        self.assertEqual(data2['word'].proper, True)

    def test_counting_forbidden(self):
        self.follow_two_publications()

        # Insert some words
        db_session.begin()
        w1 = Word(word="est", proper=False)
        w2 = Word(word="test", proper=False)
        w3 = Word(word="témoin", proper=False)
        db_session.add(w1)
        db_session.add(w2)
        db_session.add(w3)
        db_session.commit()

        db_session.begin()
        # Forbid "est" for every publication
        neverW1 = Forbidden(word_id = 1)
        # Forbid "test" for only the first publication
        notW2 = Forbidden(word_id = 2, publication_id = 1)
        db_session.add(neverW1)
        db_session.add(notW2)
        db_session.commit()

        self.create_three_frontpages()

        # Add some counters
        common_counter1 = Counter({'est' : 1, 'test' : 2, "témoin" : 3})
        common_counter2 = Counter({'est' : 4, 'test' : 5, "témoin" : 6})
        common_counter3 = Counter({'est' : 7, 'test' : 8, "témoin" : 9})
        # Serialize those counters...
        save_words(self.nfp1.id, Counter(), common_counter1)
        save_words(self.nfp2.id, Counter(), common_counter2)
        save_words(self.nfp3.id, Counter(), common_counter3)
        full_words = dict(get_all_tops()['commons'])
        # W1 should not be there
        self.assertFalse(w1.word in full_words.keys())
        # W2 should be there, but count from pub1 should be not counted
        self.assertEqual(full_words[w2.word], 8)
        # W3 should be there and fully counted
        self.assertEqual(full_words[w3.word], 18)

    def test_frequency(self):
        self.follow_two_publications()
        self.create_three_frontpages()
        common_counter1 = Counter({'rare' : 1, 'common' : 2, 'frequent' : 2})
        common_counter2 = Counter({'frequent' : 2})
        common_counter3 = Counter({'common' : 2, 'frequent' : 5})
        save_words(self.nfp1.id, Counter(), common_counter1)
        save_words(self.nfp2.id, Counter(), common_counter2)
        save_words(self.nfp3.id, Counter(), common_counter3)
        # Expected local frequency are thus :
        # For pub 1 : 
        #       Rare 1 occurence / 2 frontpages = .5
        #       Common 2 occurences / 2 frontpages = 1
        #       Frequent 4 occurences / 2 frontpages = 2
        # For pub 2:
        #       Rare  Zero occurence / 1 frontpages = 0
        #       Common  2 occurences / 1 frontpages = 2
        #       Frequent 5 occurence / 1 frontpages = 5
        # For every publications :
        #       Rare    1 occurence / 3 frontpages = 0.33
        #       Common  4 occurences / 3 frontpages = 1.33
        #       Frequence 9 occurence / 3 frontpages = 3
        resP1 = dict(count_frequency_for(self.pub1)['commons'])
        resP2 = dict(count_frequency_for(self.pub2)['commons'])
        self.assertEqual(resP1['common'], 1)
        self.assertEqual(resP1['frequent'], 2)
        self.assertEqual(resP1['rare'], .5)
        self.assertEqual(resP2['common'], 2)
        self.assertEqual(resP2['frequent'], 5)
        self.assertTrue('rare' not in resP2.keys())

    def test_timed_word(self):
        self.follow_two_publications()
        self.create_three_frontpages()
        common_counter1 = Counter({'old' : 1, 'peaking': 1})
        common_counter2 = Counter({'peaking':10})
        common_counter3 = Counter({'new' : 1, 'old':1})
        save_words(self.nfp1.id, Counter(), common_counter1)
        save_words(self.nfp2.id, Counter(), common_counter2)
        save_words(self.nfp3.id, Counter(), common_counter3)
        old = get_history_for('old')
        peaking = get_history_for('peaking')
        new = get_history_for('new')
        # Old counter is at 1 for the first day
        self.assertEqual(old[1][1], 1)
        # Peaking counter is at 1 for the first day, for the first publication
        self.assertEqual(peaking[1][1], 1)
        # Then at 10
        self.assertEqual(peaking[2][1], 10)
        # And at 0 every days for the second publication
        self.assertEqual(peaking[1][2], 0)
        self.assertEqual(peaking[1][2], 0)

if __name__ == "__main__":
    unittest.main()
