import os
import shutil
import codecs
import os.path
import traceback
from functools import partial

from carcade.conf import settings
from carcade.i18n import get_translations
from carcade.environments import create_jinja2_env, create_assets_env
from carcade.utils import sort, paginate, read_context
from carcade.exceptions import UnknownPathException, UnknownOrderingException


class Node(object):
    """Tree node."""

    def __init__(self, source_dir, name):
        self.children = []
        self.name = name
        self.source_dir = source_dir
        self.ascendant = None

    def add_child(self, node):
        self.children.append(node)
        node.ascendant = self

    def get_child(self, name):
        for child in self.children:
            if child.name == name:
                return child

        for child in self.children:
            if not isinstance(child, PageNode):
                continue
            page_child = child.get_child(name)
            if page_child:
                return page_child
    
    def get_path(self):
        names = []
        node = self
        while node.ascendant:
            names.append(node.name)
            node = node.ascendant
        return '/'.join(reversed(names))

    def get_slugs(self):
        slugs = []

        node = self
        intermediate = False
        while node.ascendant:
            slugs.append(node.get_slug(intermediate=intermediate))
            node = node.ascendant
            intermediate = True
        return reversed(slugs)

    def find_descendant(self, path):
        if '/' in path:
            child_name, rest = path.split('/', 1)
            child = self.get_child(child_name)
            return child and child.find_descendant(rest)
        else:
            return self.get_child(path)

    def get_slug(self, intermediate=False):
        if self.name == 'ROOT':
            return ''
        return self.name


class PageNode(Node):
    def __init__(self, source_dir, index):
        self.index = index
        super(PageNode, self).__init__(source_dir, settings.PAGE_NAME % index)

    def get_slug(self, intermediate=False):
        if intermediate:
            return ''
        if self.index == 1:
            return ''
        return super(PageNode, self).get_slug()


def create_tree(page_dir, page_name):
    node = Node(page_dir, page_name)

    for subpage_name in os.listdir(page_dir):
        subpage_dir = os.path.join(page_dir, subpage_name)
        if os.path.isdir(subpage_dir):
            child = create_tree(subpage_dir, subpage_name)
            node.add_child(child)

    return node


def sort_tree(node, ordering_dict):
    path = node.get_path()
    key = path and path + '/*' or '*'
    ordering = ordering_dict.get(key)

    if ordering:
        if ordering == 'alphabetically':
            node.children.sort(key=lambda child: child.name)
        elif isinstance(ordering, list):
            node.children = sort(node.children, ordering,
                                 key=lambda child: child.name)
        elif callable(ordering):
            node.children = ordering(node.children)
        else:
            raise UnknownOrderingException(key)

    node.children = [sort_tree(child, ordering_dict) for child in node.children]
    return node


def paginate_tree(node, pagination_dict):
    path = node.get_path()
    key = path and path + '/*' or '*'
    items_per_page = pagination_dict.get(key)

    if items_per_page:
        pages = paginate(node.children, items_per_page)

        node.children = []
        for index, page_items in enumerate(pages, start=1):
            page = PageNode(node.source_dir, index)
            for item in page_items:
                page.add_child(item)
            node.add_child(page)

    node.children = [
        paginate_tree(child, pagination_dict)
        for child in node.children]
    return node


def fill_tree(node, language=None):
    context = read_context(node.source_dir, language=language)

    child_contexts = []
    for child in node.children:
        fill_tree(child, language=language)
        child_contexts.append(child.context)

    context.update({
        'NAME': node.name,
        'PATH': node.get_path(),
        'LANGUAGE': language,
        'CHILDREN': child_contexts,
    })
    node.context = context

    for index, child_context in enumerate(child_contexts):
        prev_sibling = None
        if index - 1 >= 0:
            prev_sibling = child_contexts[index - 1]

        next_sibling = None
        if index + 1 < len(child_contexts):
            next_sibling = child_contexts[index + 1]

        child_context.update({
            'PARENT': context,
            'SIBLINGS': child_contexts,
            'PREV_SIBLING': prev_sibling,
            'NEXT_SIBLING': next_sibling,
        })

    return node


def build_site(jinja2_env, build_dir, node, root=None):
    for child in node.children:
        build_site(jinja2_env, build_dir, child, root=root or node)

    if node.name == 'ROOT':
        return

    path = node.get_path()
    url = url_for(root, path, language=node.context['LANGUAGE'])

    target_dir = os.path.join(build_dir, url.lstrip('/'))
    target_filename = os.path.join(target_dir, 'index.html')

    if os.path.exists(target_filename):
        return

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    layout_key = path
    if isinstance(node, PageNode):
        layout_key = node.ascendant.get_path()

    template = jinja2_env.get_template(settings.LAYOUTS[layout_key])
    template.stream(ROOT=root.context, **node.context) \
            .dump(target_filename, encoding='utf-8')


def url_for(root, path, language=None):
    """If page at `path` exists, returns it's root-relative URL;
    otherwise throws an exception.
    """
    base_url = '/'
    if language and language != settings.DEFAULT_LANGUAGE:
        base_url += '%s/' % language

    node = root.find_descendant(path)
    if not node:
        raise UnknownPathException(path)
    slugs = node.get_slugs()

    if path != settings.DEFAULT_PAGE:
        cleaned_slugs = filter(bool, slugs)
        if cleaned_slugs:
            return base_url + '/'.join(cleaned_slugs) + '/'

    return base_url


def build_(source_dir, build_dir, language=None):
    source_path = lambda *args: os.path.join(source_dir, *args)

    tree = create_tree(source_path('pages'), 'ROOT')
    tree = sort_tree(tree, settings.ORDERING)
    tree = paginate_tree(tree, settings.PAGINATION)
    tree = fill_tree(tree, language=language)

    translations = None
    if language:
        translations_path = source_path('translations/%s.po' % language)
        if os.path.exists(translations_path):
            translations = get_translations(translations_path)

    assets_env = create_assets_env(
        source_path('static'), build_dir, settings.BUNDLES)
    jinja2_env = create_jinja2_env(
        url_for=partial(url_for, tree),
        assets_env=assets_env,
        translations=translations)

    build_site(jinja2_env, build_dir, tree)


def build(source_dir, build_dir):
    shutil.copytree(os.path.join(source_dir, 'static'), build_dir)
    try:
        if settings.LANGUAGES:
            for language in settings.LANGUAGES:
                build_(source_dir, build_dir, language=language)
        else:
            build_(source_dir, build_dir)
    except Exception:
        shutil.rmtree(build_dir)
        raise
