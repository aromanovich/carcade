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


class Page(object):
    def __init__(self, name, target_filename, context):
        self.name = name
        self.context = context
        self.target_filename = target_filename
        self.children = []
        self.ascendant = None

    def add_child(self, page):
        self.children.append(page)
        page.ascendant = self


def build(build_dir):
    PAGES_DIR = 'pages/'

    for language in carcade_settings.LANGUAGES:
        jinja2_env = create_jinja2_environment(language)
        
        # Build site tree from down to top
        forest = {}  # `forest` contains growing site subtrees
        for root, directories, files in os.walk(PAGES_DIR, topdown=False):
            page_name = root[len(PAGES_DIR):]

            context = create_context(root, language)
            context['PAGE_NAME'] = page_name

            target_filename = os.path.join(
                build_dir, path_for(page_name, language=language), 'index.html')

            page = Page(page_name, target_filename, context)
            for directory in directories:
                child_name = os.path.join(page_name, directory)
                child = forest.pop(child_name)  # Pop subtree from `forest`
                page.add_child(child)  # Attach it to ascendant page

            forest[page.name] = page  # Put resulting subtree to the `forest`

        root = forest.pop('')
        assert not forest

        build_recursive(jinja2_env, root)


def build_recursive(jinja2_env, page):
    for child in page.children:
        build_recursive(jinja2_env, child)

    if not page.name:
        # `page` is root, nothing to build
        return

    # Retrieve template
    template = jinja2_env.get_template(
        carcade_settings.LAYOUTS.get(page.name, carcade_settings.DEFAULT_LAYOUT))

    # Collect descendant page contexts
    subpages = []
    for subpage in page.children:
        subpages.append(subpage.context)

    # Collect sibling page contexts
    index = None
    siblings = []
    for idx, sibling in enumerate(page.ascendant.children):
        if sibling == page:  # TODO Introduce pagination
            index = idx
        siblings.append(sibling.context)

    # Important: don't change stored context by adding new keys
    context = dict(page.context, **{
        'SUBPAGES': subpages,  # TODO Make naming more consistent
        'SIBLINGS': siblings,
        'INDEX': index  # XXX
    })
    render_template(template, context, page.target_filename)
