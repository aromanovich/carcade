import os
import sys
import glob
import codecs
import gettext
import os.path
import tempfile

import polib
import yaml
import markdown
from jinja2 import Environment, FileSystemLoader, contextfunction
from webassets import Environment as AssetsEnvironment


class Node(object):
    def __init__(self):
        self.children = []
        self.ascendant = None

    def add_child(self, page):
        self.children.append(page)
        page.ascendant = self

    def render(self, jinja2_env, build_directory):
        for child in self.children:
            child.render(jinja2_env, build_directory)


class Page(Node):
    def __init__(self, pages_root, page_directory, language):
        super(Page, self).__init__()
        self.source_directory = page_directory
        self.name = os.path.relpath(self.source_directory, pages_root)
        self.language = language
        self.context = {
            'PAGE_NAME': self.name
        }

        for f in self._data_files('md'):
            var_name, suffix = os.path.basename(f.name).split('.', 1)
            self.context[var_name] = markdown.markdown(f.read())

        for f in self._data_files('yaml'):
            data = yaml.load(f.read())
            if data:
                self.context.update(data)

    def _data_files(self, extension):
        pattern = '*.%s.%s' % (self.language, extension)
        for filename in glob.glob(os.path.join(self.source_directory, pattern)):
            with codecs.open(filename, 'r', 'utf-8') as f:
                yield f

    def render(self, jinja2_env, build_directory):
        super(Page, self).render(jinja2_env, build_directory)

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

        target_filename = os.path.join(
            build_directory, path_for(self.name, language=self.language), 'index.html')

        target_directory = os.path.dirname(target_filename)
        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        with codecs.open(target_filename, 'w', 'utf-8') as f:
            f.write(template.render(**context))


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


def create_jinja2_environment(build_directory, language):
    jinja2_env = Environment(
        loader=FileSystemLoader('layouts'),
        extensions=['jinja2.ext.i18n', 'webassets.ext.jinja2.AssetsExtension'])

    assets_env = AssetsEnvironment()
    assets_env.load_path = ['static']
    assets_env.directory = build_directory
    assets_env.url = '/'
    assets_env.manifest = False
    assets_env.cache = False
    for bundle_name, bundle in carcade_settings.BUNDLES.iteritems():
        assets_env.register(bundle_name, bundle)
    jinja2_env.assets_environment = assets_env

    try:
        po_file = polib.pofile('./translations/%s.po' % language)
        with tempfile.NamedTemporaryFile() as mo_file:
            po_file.save_as_mofile(mo_file.name)
            translations = gettext.GNUTranslations(mo_file)
        jinja2_env.install_gettext_translations(translations, newstyle=True)
    except IOError:
        jinja2_env.install_null_translations(newstyle=True)

    jinja2_env.globals.update(url_for=url_for, LANGUAGE=language)
    return jinja2_env


def create_tree(pages_root, language):
    # Build site tree from down to top
    forest = {}  # `forest` contains growing site subtrees
    for page_directory, directories, files in os.walk(pages_root, topdown=False):
        if page_directory == pages_root:
            # Reached the top. We're done
            break

        page = Page(pages_root, page_directory, language)
        for directory in directories:
            subpage_directory = os.path.join(page_directory, directory)
            subpage = forest.pop(subpage_directory)  # Pop subtree from `forest`
            page.add_child(subpage)  # Attach it to ascendant page

        forest[page_directory] = page  # Put resulting subtree to the `forest`

    root = Node()
    for page in forest.values():
        root.add_child(page)
    return root


def build(carcade_settings_, build_directory):
    global carcade_settings  # XXX!!!
    carcade_settings = carcade_settings_
    for language in carcade_settings.LANGUAGES:
        jinja2_env = create_jinja2_environment(build_directory, language)
        root = create_tree('./pages/', language)
        root.render(jinja2_env, build_directory)
