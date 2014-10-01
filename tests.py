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
                <h1>What I want</h1><div><p> is this.</p></div></body>"""
        res = just_content(page)
        self.assertEqual(res, "What I want is this.")
        # We want to make sure MULTIPLE scripts are removed
        page = """<html><body><script>don't want this</script>
                  <script>nor this</script><p>I want this.</script>"""
        res = just_content(page)
        self.assertEqual(res, "I want this.")

if __name__ == "__main__":
    unittest.main()
