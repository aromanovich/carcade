import os
import re
import shutil
import codecs
import os.path
from functools import partial

from carcade.conf import settings
from carcade.i18n import get_translations
from carcade.environments import create_jinja2_env, create_assets_env
from carcade.utils import sort, paginate, read_context


class Node(object):
    """Tree node."""

    def __init__(self, source_dir, name):
        self.children = []
        self.name = name
        self.source_dir = source_dir

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

    def get_slug(self):
        if self.name == 'ROOT':
            return ''
        return self.name


class PageNode(Node):
    def __init__(self, source_dir, index):
        self.index = index
        super(PageNode, self).__init__(source_dir, settings.PAGE_NAME % index)

    def get_slug(self):
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


def sort_tree(node, ordering_dict, path=[]):
    key = '/'.join(path + ['*'])
    ordering = ordering_dict.get(key)

    if ordering == 'alphabetically':
        node.children.sort(key=lambda child: child.name)
    elif isinstance(ordering, list):
        node.children = sort(node.children, ordering,
                             key=lambda child: child.name)
    else:
        pass  # TODO

    node.children = [
        sort_tree(child, ordering_dict, path=path + [child.name])
        for child in node.children]
    return node


def paginate_tree(node, pagination_dict, path=[]):
    key = '/'.join(path + ['*'])
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
        paginate_tree(child, pagination_dict, path=path + [child.name])
        for child in node.children]
    return node


def fill_tree(node, language=None, path=[]):
    context = read_context(node.source_dir, language=language)

    child_contexts = []
    for child in node.children:
        fill_tree(child, language=language, path=path + [child.name])
        child_contexts.append(child.context)

    context.update({
        'NAME': node.name,
        'PATH': '/'.join(path),
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


def build_tree(jinja2_env, build_dir, node, root=None, path=[]):
    for child in node.children:
        build_tree(jinja2_env, build_dir, child,
                   root=root or node, path=path + [child.name])

    if node.name == 'ROOT':
        return

    path_str = '/'.join(path)
    url = url_for(root, path_str, language=node.context['LANGUAGE'])

    target_dir = os.path.join(build_dir, url.lstrip('/'))
    target_filename = os.path.join(target_dir, 'index.html')

    if os.path.exists(target_filename):
        return

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    if isinstance(node, PageNode):
        layout_key = '/'.join(path[:-1])
    else:
        layout_key = path_str

    layout = settings.DEFAULT_LAYOUT
    for pattern, layout_path in settings.LAYOUTS.items():
        if re.match(pattern, layout_key):
            layout = layout_path

    template = jinja2_env.get_template(layout)
    with codecs.open(target_filename, 'w', 'utf-8') as target_file:
        context = dict(node.context, ROOT=root.context)
        target_file.write(template.render(**context))


def get_slugs(node, path=[]):
    """If page at `path` exists, returns slugs of the nodes lies on that path;
    otherwise throws an exception.
    """
    slug = node.get_slug()

    if not path:  # Recursion base
        return [slug]

    if isinstance(node, PageNode):
        slug = ''

    head, rest = path[0], path[1:]
    child = node.get_child(head)
    if not child:
        pass  # TODO Raise error
    return [slug] + get_slugs(child, path=rest)


def url_for(tree, path_str, language=None):
    """If page at `path` exists, returns it's root-relative URL;
    otherwise throws an exception.
    """
    base_url = '/'
    if language and language != settings.DEFAULT_LANGUAGE:
        base_url += '%s/' % language

    slugs = get_slugs(tree, path=path_str.split('/'))

    if path_str != settings.DEFAULT_PAGE:
        cleaned_slugs = filter(bool, slugs)
        return base_url + '/'.join(cleaned_slugs) + '/'
    else:
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

    build_tree(jinja2_env, build_dir, tree)


def build(source_dir, build_dir):
    shutil.copytree(os.path.join(source_dir, 'static'), build_dir)
    try:
        if settings.LANGUAGES:
            for language in settings.LANGUAGES:
                build_(source_dir, build_dir, language=language)
        else:
            build_(source_dir, build_dir)
    except Exception as e:
        shutil.rmtree(build_dir)
        raise e
