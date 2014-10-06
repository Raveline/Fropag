import unittest
from collections import Counter
from reader import *
import config
from core import *
from sqlalchemy import func

class DBTesting(unittest.TestCase):
    def setUp(self):
        config.DB_NAME = "testFropag"
        config.DB_USER = "testUser"
        config.DB_PASSWORD = "testPwd"
        init_db()
        self.session = get_session()

    def tearDown(self):
        eng = get_engine()
        Base.metadata.drop_all(eng)

class DatabaseOperations(DBTesting):

    def test_follow_publication(self):
        test_url = "http://test.test"
        test_name = "Test publication"
        follow_publication(test_name, test_url, "start", "end")
        try:
            # The proper publication has been inserted
            q = self.session.query(Publication).filter(Publication.name == test_name).one()
            self.assertEqual(q.url, test_url)
            # Only one publication has been inserted
            self.assertEqual(1, self.session.query(Publication).count())
        except:
            self.fail("Couldn't fetch ONE result for query.")

    def test_get_words(self):
        # Insert some publications
        follow_publication("Test1", "", "", "")
        follow_publication("Test2", "", "", "")
        pub1 = self.session.query(Publication).filter(Publication.name == "Test1").one().id
        pub2 = self.session.query(Publication).filter(Publication.name == "Test2").one().id
        # Frontpage 1 and 2 for pub1
        nfp1 = FrontPage(publication_id = pub1) 
        nfp2 = FrontPage(publication_id = pub1)
        # Frontpage 3 for pub2
        nfp3 = FrontPage(publication_id = pub2)
        self.session.add(nfp1)
        self.session.add(nfp2)
        self.session.add(nfp3)
        # Counters to use
        proper_counter1 = Counter({'proper1' : 1})
        common_counter1 = Counter({'word1' : 2, 'word2' : 1})
        common_counter2 = Counter({'word1' : 1, 'word3' : 4})
        proper_counter2 = Counter({'proper1' : 1, 'proper2' : 2})
        common_counter3 = Counter({'word1' : 12, 'word4' : 2})
        proper_counter3 = Counter({'proper3' : 2})
        # Serialize those counters...
        save_words(self.session, nfp1.id, proper_counter1, common_counter1)
        save_words(self.session, nfp2.id, proper_counter2, common_counter2)
        save_words(self.session, nfp3.id, proper_counter3, common_counter3)
        # Here we are !
        result = see_words_for("Test1")
        self.assertTrue('word1' in result)
        self.assertFalse('word4' in result, "Only words in this publication should be there")

class TestPageReader(unittest.TestCase):
    def test_access_page(self):
        res = access_page("http://www.google.com")
        self.assertNotEqual(res.find("google.timers"), 0)

    def test_just_content(self):
        # We want to make sure script are removed.
        page = """<html><head><head>...blabla...</head><body>
                <script>Some javascript</script>
                <style>Things I should not see</style>
                <h1>What I want</h1><div><p>is this.</p></div></body>"""
        res = just_content(page)
        self.assertEqual(res, "What I want is this.")
        # We want to make sure MULTIPLE scripts are removed
        page = """<html><body><script>don't want this</script>
                  <style>Things I shouln't see</style>
                  <script>nor this</script><p>I want this.</script>"""
        res = just_content(page)
        self.assertEqual(res, "I want this.")

    def test_cut_between_normal(self):
        text = "Shall I compare thee to a summer day ? Thou art more lovely"
        text2 = cut_between(text, "thee", "?")
        self.assertEqual(text2, "to a summer day")

    def test_cut_from_not_there(self):
        text = "Shall I compare thee"
        text2 = cut_between(text, "hamburger", "thee")
        self.assertEqual(text2, "Shall I compare")

    def test_cut_to_not_there(self):
        text = "Shall I compare thee to a summer day"
        text2 = cut_between(text, "compare", "hamburger")
        self.assertEqual(text2, "thee to a summer day")
        
if __name__ == "__main__":
    unittest.main()
