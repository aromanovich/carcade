import os
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

    def render(self, jinja2_env, build_dir):
        for child in self.children:
            child.render(jinja2_env, build_dir)


class Page(Node):
    def __init__(self, pages_root, page_dir, language=None):
        super(Page, self).__init__()
        self.source_dir = page_dir
        self.name = os.path.relpath(self.source_dir, pages_root)
        self.language = language
        self.context = {
            'PAGE_NAME': self.name
        }

        for file in self._data_files('md'):
            var_name, suffix = os.path.basename(file.name).split('.', 1)
            self.context[var_name] = markdown.markdown(file.read())

        for file in self._data_files('yaml'):
            data = yaml.load(file.read())
            if data:
                self.context.update(data)

    def _data_files(self, extension):
        pattern = '*'
        if self.language:
            pattern += '.%s' % self.language
        pattern += '.%s' % extension

        for filename in glob.glob(os.path.join(self.source_dir, pattern)):
            with codecs.open(filename, 'r', 'utf-8') as file:
                yield file

    def render(self, jinja2_env, build_dir):
        super(Page, self).render(jinja2_env, build_dir)

        # Retrieve template
        template = jinja2_env.get_template(carcade_settings.LAYOUTS[self.name])

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
            build_dir, path_for(self.name, language=self.language), 'index.html')

        target_dir = os.path.dirname(target_filename)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        with codecs.open(target_filename, 'w', 'utf-8') as file:
            file.write(template.render(**context))


def path_for(name, language=None):
    url = ''
    if language and language != carcade_settings.DEFAULT_LANGUAGE:
        url += '%s/' % language
    if name != carcade_settings.DEFAULT_PAGE:
        url += '%s/' % name
    return url


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
    for bundle_name, bundle in carcade_settings.BUNDLES.iteritems():
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


def create_tree(pages_root, language=None):
    # Build site tree from down to top
    forest = {}  # `forest` contains growing site subtrees
    for page_dir, dirs, files in os.walk(pages_root, topdown=False):
        if page_dir == pages_root:
            # Reached the top. We're done
            break

        page = Page(pages_root, page_dir, language=language)
        for dir in dirs:
            subpage_dir = os.path.join(page_dir, dir)
            subpage = forest.pop(subpage_dir)  # Pop subtree from `forest`
            page.add_child(subpage)  # Attach it to ascendant page

        forest[page_dir] = page  # Put resulting subtree to the `forest`

    root = Node()
    for page in forest.values():
        root.add_child(page)
    return root


def build(carcade_settings_, build_dir):
    global carcade_settings  # XXX!!!
    carcade_settings = carcade_settings_

    for language in getattr(carcade_settings, 'LANGUAGES', [None]):
        jinja2_env = create_jinja2_environment(build_dir, language=language)
        root = create_tree('./pages/', language=language)
        root.render(jinja2_env, build_dir)
