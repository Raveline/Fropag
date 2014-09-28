import unittest
from collections import Counter
from fropag import *

class TestPageReader(unittest.TestCase):
    def test_access_page(self):
        res = access_page("http://www.google.com")
        self.assertNotEqual(res.find("google.timers"), 0)

    def test_just_content(self):
        # We want to make sure script are removed.
        page = """<html><head><head>...blabla...</head><body>
                <script>Some javascript</script>
                <h1>What I want</h1><div><p> is this.</p></div></body>"""
        res = just_content(page)
        self.assertEqual(res, "What I want is this.")
        # We want to make sure MULTIPLE scripts are removed
        page = """<html><body><script>don't want this</script>
                  <script>nor this</script><p>I want this.</script>"""
        res = just_content(page)
        self.assertEqual(res, "I want this.")

    def test_just_words(self):
        basic = "The heart is a lonely hunter."
        basic_ok = "the heart is a lonely hunter"
        double = "The heart: a lonely hunter ?"
        double_ok = "the heart  a lonely hunter"
        apostrophe = "The heart's lonely hunterness"
        apostrophe_ok = "the heart s lonely hunterness"
        hyphen = "The lonely-hunter"
        hyphen_ok = "the lonely-hunter"
        unicoded = u"Un pas de sénateur élégant"
        unicoded_ok = u"un pas de sénateur élégant"
        
        self.assertEqual(just_words(basic), basic_ok)
        self.assertEqual(just_words(double), double_ok)
        self.assertEqual(just_words(apostrophe), apostrophe_ok)
        self.assertEqual(just_words(hyphen), hyphen_ok)
        self.assertEqual(just_words(unicoded), unicoded_ok)
        self.assertEqual(just_words(unicoded2), unicoded2_ok)

    def test_to_word_counter(self):
        # simple case
        text = "this is a test test test"
        counter = to_word_counter(just_words(text))
        self.assertEqual(counter['this'], 1)
        self.assertEqual(counter['test'], 3)

if __name__ == "__main__":
    unittest.main()
