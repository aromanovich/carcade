import gettext
import tempfile

import polib
import jinja2
import webassets

from carcade.conf import settings
from carcade.utils import path_for


def create_assets_environment(build_dir):
    env = webassets.Environment()
    env.config.update({
        'load_path': ['static'],
        'directory': build_dir,
        'url': '/',
        'manifest': False,
        'cache': False,
    })
    for bundle_name, bundle in settings.BUNDLES.iteritems():
        env.register(bundle_name, bundle)
    return env


def get_translations(language):
    try:
        po_file = polib.pofile('./translations/%s.po' % language)
        with tempfile.NamedTemporaryFile() as mo_file:
            po_file.save_as_mofile(mo_file.name)
            return gettext.GNUTranslations(mo_file)
    except IOError:
        return None


def url_for(name, language=None):
    language = language or context.resolve('LANGUAGE')
    return '/' + path_for(name, language=language)


@jinja2.contextfunction
def jinja2_url_for(context, name, language=None):
    language = language or context.resolve('LANGUAGE')
    return url_for(name, language=language)


def create_jinja2_environment(build_dir, language=None):
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('layouts'),
        extensions=['jinja2.ext.i18n', 'webassets.ext.jinja2.AssetsExtension'])
    env.globals.update(url_for=jinja2_url_for)

    env.assets_environment = create_assets_environment(build_dir)

    env.install_null_translations(newstyle=True)
    if language:
        env.globals.update(LANGUAGE=language)
        translations = get_translations(language)
        if translations:
            env.install_gettext_translations(translations, newstyle=True)

    return env
