import unittest
from collections import Counter
from reader import *

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
