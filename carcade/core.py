import os
import sys
import glob
import codecs
import gettext

import yaml
import markdown
from jinja2 import Environment, FileSystemLoader, contextfunction

sys.path.append(os.getcwd())
import carcade_settings


PAGES_PREFIX = 'pages/'


def path_for(name, language=None):
    url = ''
    if language != carcade_settings.DEFAULT_LANGUAGE:
        url += '%s/' % language
    if name != carcade_settings.DEFAULT_PAGE:
        url += '%s/' % name
    return url


@contextfunction
def url_for(context, name, language=None):
    language = language or context.resolve('LANGUAGE')
    return '/' + path_for(name, language=language)


def create_jinja2_environment(language):
    env = Environment(loader=FileSystemLoader('layouts'),
                      extensions=['jinja2.ext.i18n'])
    try:
        with open('./translations/%s.mo' % language) as translations_file:
            translations = gettext.GNUTranslations(translations_file)
        env.install_gettext_translations(translations, newstyle=True)
    except IOError:
        env.install_null_translations(newstyle=True)

    env.globals.update(url_for=url_for, LANGUAGE=language)
    return env


def render_template(template, context, target_fname):
    target_dir = os.path.dirname(target_fname)
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    render = template.render(**context)
    with codecs.open(target_fname, 'w', 'utf-8') as f:
        f.write(render)


def page_files(page_dir, language, md_or_yaml):
    """Yields files from `page_dir` which names matched to
    `*.<language>.<md|yaml>` pattern.
    """
    assert md_or_yaml in ('md', 'yaml')
    pattern = '*.%s.%s' % (language, md_or_yaml)
    for filename in glob.glob(os.path.join(page_dir, pattern)):
        with codecs.open(filename, 'r', 'utf-8') as f:
            yield f


def create_context(page_dir, language):
    """Creates context by parsing all markdown- and yaml-files with given
    `language` from `page_dir`.
    """
    context = {}

    for f in page_files(page_dir, language, 'md'):
        var_name, suffix = os.path.basename(f.name).split('.', 1)
        context[var_name] = markdown.markdown(f.read())

    for f in page_files(page_dir, language, 'yaml'):
        data = yaml.load(f.read())
        if data:
            context.update(data)

    return context


def build(build_dir):
    for language in carcade_settings.LANGUAGES:
        contexts = {}
        jinja2_env = create_jinja2_environment(language)

        for root, directories, files in os.walk(PAGES_PREFIX, topdown=False):
            page_name = root[len(PAGES_PREFIX):]

            if not page_name:
                # Reached the top. We're done
                break

            context = create_context(root, language)
            context['PAGE_NAME'] = page_name

            # Store context — we will need it to construct ascendant page context
            contexts[page_name] = context

            # Retrieve template
            template = jinja2_env.get_template(
                carcade_settings.LAYOUTS.get(page_name, carcade_settings.DEFAULT_LAYOUT))

            subpages = []
            for directory in directories:
                # Collect descendant page contexts into `subpages` list
                subpage_name = os.path.join(page_name, directory)
                subpages.append(contexts[subpage_name])

            target_filename = os.path.join(
                build_dir, path_for(page_name, language=language), 'index.html')
            # Important: don't change stored context by adding `SUBPAGES`
            context = dict(context, SUBPAGES=subpages)
            render_template(template, context, target_filename)
