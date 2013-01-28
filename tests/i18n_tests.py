import unittest
import tempfile

import polib

from carcade.environments import create_jinja2_env
from carcade.i18n import extract_translations


class TranslationsExtractionTest(unittest.TestCase):
    def test(self):
        jinja2_env = create_jinja2_env(layouts_dir='tests/fixtures/layouts')

        with tempfile.NamedTemporaryFile() as pot_file:
            extract_translations(jinja2_env, pot_file.name)
            po_entries = polib.pofile(pot_file.name)
            
            self.assertEqual(
                str(po_entries[0]),
                '#: test.html:1\n'
                'msgid "Static"\n'
                'msgstr "Static"\n')
            
            self.assertEqual(
                str(po_entries[1]),
                '#: test.html:1 test.html:3\n'
                'msgid "sites"\n'
                'msgstr "sites"\n')
