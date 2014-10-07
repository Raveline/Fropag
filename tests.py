import unittest
from collections import Counter
from reader import *
import config
from core import *
from database import *
from sqlalchemy import func
from sqlalchemy.orm import sessionmaker, scoped_session

class DBTesting(unittest.TestCase):
    def setUp(self):
        config.DB_NAME = "testFropag"
        config.DB_USER = "testUser"
        config.DB_PASSWORD = "testPwd"
        global engine, db_session
        engine = get_engine()
        db_session = scoped_session(sessionmaker(bind=engine))
        init_db()

    def tearDown(self):
        Base.metadata.drop_all(engine)

class DatabaseOperations(DBTesting):

    def test_follow_publication(self):
        test_url = "http://test.test"
        test_name = "Test publication"
        follow_publication(test_name, test_url, "start", "end")
        try:
            # The proper publication has been inserted
            q = db_session.query(Publication).filter(Publication.name == test_name).one()
            self.assertEqual(q.url, test_url)
            # Only one publication has been inserted
            self.assertEqual(1, db_session.query(Publication).count())
        except:
            self.fail("Couldn't fetch ONE result for query.")

    def test_get_words(self):
        # Insert some publications
        follow_publication("Test1", "", "", "")
        follow_publication("Test2", "", "", "")
        pub1 = db_session.query(Publication).filter(Publication.name == "Test1").one().id
        pub2 = db_session.query(Publication).filter(Publication.name == "Test2").one().id
        # Frontpage 1 and 2 for pub1
        nfp1 = FrontPage(publication_id = pub1) 
        nfp2 = FrontPage(publication_id = pub1)
        # Frontpage 3 for pub2
        nfp3 = FrontPage(publication_id = pub2)
        db_session.add(nfp1)
        db_session.add(nfp2)
        db_session.add(nfp3)
        db_session.commit()
        # Counters to use
        proper_counter1 = Counter({'proper1' : 1})
        common_counter1 = Counter({'word1' : 2, 'word2' : 1})
        common_counter2 = Counter({'word1' : 1, 'word3' : 4})
        proper_counter2 = Counter({'proper1' : 1, 'proper2' : 2})
        common_counter3 = Counter({'word1' : 12, 'word4' : 2})
        proper_counter3 = Counter({'proper3' : 2})
        # Serialize those counters...
        save_words(nfp1.id, proper_counter1, common_counter1)
        save_words(nfp2.id, proper_counter2, common_counter2)
        save_words(nfp3.id, proper_counter3, common_counter3)
        # Here we are !
        result = dict(see_words_for("Test1", False))
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

if __name__ == "__main__":
    unittest.main()
