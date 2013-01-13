import gettext
import tempfile

import polib
from webassets import Environment as AssetsEnvironment
from jinja2 import Environment, FileSystemLoader, contextfunction

from carcade.conf import settings
from carcade.utils import path_for


@contextfunction
def url_for(context, name, language=None):
    language = language or context.resolve('LANGUAGE')
    return '/' + path_for(name, language=language)


def create_assets_environment(build_dir):
    assets_env = AssetsEnvironment()
    assets_env.config.update({
        'load_path': ['static'],
        'directory': build_dir,
        'url': '/',
        'manifest': False,
        'cache': False,
    })
    for bundle_name, bundle in settings.BUNDLES.iteritems():
        assets_env.register(bundle_name, bundle)
    return assets_env


def get_translations(language):
    try:
        po_file = polib.pofile('./translations/%s.po' % language)
        with tempfile.NamedTemporaryFile() as mo_file:
            po_file.save_as_mofile(mo_file.name)
            return gettext.GNUTranslations(mo_file)
    except IOError:
        return None


def create_jinja2_environment(build_dir, language=None):
    jinja2_env = Environment(
        loader=FileSystemLoader('layouts'),
        extensions=['jinja2.ext.i18n', 'webassets.ext.jinja2.AssetsExtension'])
    jinja2_env.globals.update(url_for=url_for)

    jinja2_env.assets_environment = create_assets_environment(build_dir)

    jinja2_env.install_null_translations(newstyle=True)
    if language:
        jinja2_env.globals.update(LANGUAGE=language)
        translations = get_translations(language)
        if translations:
            jinja2_env.install_gettext_translations(translations, newstyle=True)

    return jinja2_env
