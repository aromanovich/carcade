import gettext
import tempfile

import polib


def get_translations(po_file_path):
    """Creates :class:`gettext.GNUTranslations` from PO file `po_file_path`."""
    po_file = polib.pofile(po_file_path)
    with tempfile.NamedTemporaryFile() as mo_file:
        po_file.save_as_mofile(mo_file.name)
        return gettext.GNUTranslations(mo_file)
