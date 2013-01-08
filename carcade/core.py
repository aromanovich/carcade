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


PAGES_DIR = 'pages/'


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


def page_files(page_dir, language, md_or_yaml):
    """Yields files from `page_dir` which names matched to
    `*.<language>.<md|yaml>` pattern.
    """
    assert md_or_yaml in ('md', 'yaml')
    pattern = '*.%s.%s' % (language, md_or_yaml)
    for filename in glob.glob(os.path.join(page_dir, pattern)):
        with codecs.open(filename, 'r', 'utf-8') as f:
            yield f


class Node(object):
    def __init__(self):
        self.children = []
        self.ascendant = None

    def add_child(self, page):
        self.children.append(page)
        page.ascendant = self

    def build(self, jinja2_env, build_directory):
        for child in self.children:
            child.build(jinja2_env, build_directory)


class Page(Node):
    def __init__(self, page_dir, language):
        super(Page, self).__init__()
        self.name = page_dir[len(PAGES_DIR):]
        self.context = {'PAGE_NAME': self.name}

        for f in page_files(page_dir, language, 'md'):
            var_name, suffix = os.path.basename(f.name).split('.', 1)
            self.context[var_name] = markdown.markdown(f.read())

        for f in page_files(page_dir, language, 'yaml'):
            data = yaml.load(f.read())
            if data:
                self.context.update(data)

    def get_target_filename(self, build_dir, language):
        return os.path.join(
            build_dir, path_for(self.name, language=language), 'index.html')

    def build(self, jinja2_env, build_directory):
        super(Page, self).build(jinja2_env, build_directory)

        # Retrieve template
        template = jinja2_env.get_template(
            carcade_settings.LAYOUTS.get(self.name, carcade_settings.DEFAULT_LAYOUT))

        # Collect descendant page contexts
        subpages = []
        for subpage in self.children:
            subpages.append(subpage.context)

        # Collect sibling page contexts
        index = None
        siblings = []
        for idx, sibling in enumerate(self.ascendant.children):
            if sibling == self:  # TODO Introduce pagination
                index = idx
            siblings.append(sibling.context)

        context = dict(self.context, **{
            'SUBPAGES': subpages,  # TODO Make naming more consistent
            'SIBLINGS': siblings,
            'INDEX': index  # XXX
        })
        self.render_template(template, context, build_directory)

    def render(self, template, context, build_directory):
        target_filename = self.get_target_filename(
            build_directory, template.globals['LANGUAGE'])
        target_dir = os.path.dirname(target_filename)

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        with codecs.open(target_filename, 'w', 'utf-8') as f:
            f.write(template.render(**context))


def build(build_dir):
    for language in carcade_settings.LANGUAGES:
        jinja2_env = create_jinja2_environment(language)

        # Build site tree from down to top
        forest = {}  # `forest` contains growing site subtrees
        for root, directories, files in os.walk(PAGES_DIR, topdown=False):
            if root == PAGES_DIR:
                break

            page = Page(root, language)
            for directory in directories:
                child_name = os.path.join(page.name, directory)
                child = forest.pop(child_name)  # Pop subtree from `forest`
                page.add_child(child)  # Attach it to ascendant page

            forest[page.name] = page  # Put resulting subtree to the `forest`

        root = Node()
        for page in forest.values():
            root.add_child(page)
        root.build(jinja2_env, build_dir)
