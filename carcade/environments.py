import jinja2
import webassets


def create_assets_env(source_dir, build_dir, bundles):
    """Creates webassets environment with registered `bundles`.

    :param source_dir: directory that will be searched for source files
    :param build_dir: output directory (bundle's `output` will be treated
                      relative to it)
    :param bundles: dictionary with bundle names as keys and to bundles
                    (:class:`webassets.Bundle`) as values
    """
    env = webassets.Environment()
    env.config.update({
        'load_path': [source_dir],
        'directory': build_dir,
        'url': '/',
        'manifest': False,
        'cache': False,
    })
    for bundle_name, bundle in bundles.iteritems():
        env.register(bundle_name, bundle)
    return env


def create_jinja2_url_for(url_for):
    def jinja2_url_for(context, path, language=None):
        """Returns URL of the page with `path` in a specified language.
        If language isn't specified, then it's taken from current template
        context.
        """
        language = language or context.resolve('LANGUAGE')
        return url_for(path, language=language)
    return jinja2.contextfunction(jinja2_url_for)


def create_jinja2_env(url_for=None, translations=None, assets_env=None,
                      layouts_dir='layouts'):
    """Creates :class:`jinja2.Environment`. Installs `translations` if
    specified; installs webassets extension with `assets_env` if specified.

    :type translations: :class:`gettext.GNUTranslations`
    :type assets_env: :class:`webassets.Environment`
    """
    jinja2_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(layouts_dir),
        extensions=['jinja2.ext.i18n'])
    jinja2_env.install_null_translations(newstyle=True)

    if url_for:
        jinja2_env.globals.update({
            'url_for': create_jinja2_url_for(url_for),
        })

    if assets_env is not None:
        # :class:`webassets.env.Environment` evaluates to False in boolean context :/
        jinja2_env = jinja2_env.overlay(
            extensions=['webassets.ext.jinja2.AssetsExtension'])
        jinja2_env.assets_environment = assets_env

    if translations:
        jinja2_env.install_gettext_translations(translations, newstyle=True)

    return jinja2_env
