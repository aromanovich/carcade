import gettext
import tempfile
from collections import defaultdict

import polib

from carcade.utils import get_template_source


def get_translations(po_file_path):
    """Creates :class:`gettext.GNUTranslations` from PO file `po_file_path`."""
    po_file = polib.pofile(po_file_path)
    with tempfile.NamedTemporaryFile() as mo_file:
        po_file.save_as_mofile(mo_file.name)
        return gettext.GNUTranslations(mo_file)


def extract_translations(jinja2_env, target_pot_file):
    """Produces a `target_pot_file` which contains a list of all
    the translatable strings extracted from the templates.
    """
    po = polib.POFile()
    po.metadata = {'Content-Type': 'text/plain; charset=utf-8'}

    messages = defaultdict(list)
    for template in jinja2_env.list_templates():
        template_source = get_template_source(jinja2_env, template)
        for (lineno, _, message) in jinja2_env.extract_translations(template_source):
            message = unicode(message)
            occurence = (template, lineno)
            messages[message].append(occurence)

    for message, occurrences in messages.iteritems():
        entry = polib.POEntry(msgid=message, msgstr=message, occurrences=occurrences)
        po.append(entry)

    po.save(target_pot_file)
