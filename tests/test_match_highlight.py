"""Match highlight helpers for search-it partial matches."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.match_highlight import escape_html, highlight_mac_match, highlight_text_match


class TestMatchHighlight(unittest.TestCase):
    def test_escape_html(self):
        self.assertEqual(escape_html('<b>&'), '&lt;b&gt;&amp;')

    def test_highlight_text_match_case_insensitive(self):
        html = highlight_text_match('Uplink to CORE', 'link')
        self.assertIn('<mark class="nst-match">link</mark>', html)
        self.assertIn('Up', html)

    def test_highlight_text_no_match(self):
        html = highlight_text_match('foo', 'bar')
        self.assertNotIn('mark', html)
        self.assertEqual(html, 'foo')

    def test_highlight_mac_partial(self):
        html = highlight_mac_match('aa:bb:cc:dd:ee:ff', 'aabb')
        self.assertIn('<mark class="nst-match">', html)
        self.assertIn('aa', html)
        self.assertIn('bb', html)

    def test_highlight_mac_no_match(self):
        html = highlight_mac_match('aa:bb:cc:dd:ee:ff', 'ffff')
        self.assertNotIn('mark', html)


if __name__ == '__main__':
    unittest.main()
