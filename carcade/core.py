import os
import codecs
import os.path
from itertools import izip_longest

import yaml
import markdown

from carcade.conf import settings
from carcade.utils import path_for
from carcade.i18n import get_translations
from carcade.environments import create_jinja2_env, create_assets_env
from carcade.utils import yield_files


class Node(object):
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
        return None


def create_tree(page_dir, page_name):
    node = Node(page_dir, page_name)

    for subpage_name in os.listdir(page_dir):
        subpage_dir = os.path.join(page_dir, subpage_name)
        if os.path.isdir(subpage_dir):
            child = create_tree(subpage_dir, subpage_name)
            node.add_child(child)

    return node


def order_tree(node, ordering_dict, track=[]):
    key = '/'.join(track + ['*'])
    ordering = ordering_dict.get(key)

    if ordering == 'alphabetically':
        node.children.sort(key=lambda el: el.name)
    elif isinstance(ordering, list):
        def key(el):
            if el.name in ordering:
                return ordering.index(el.name)
            else:
                return len(ordering) + 1
        node.children.sort(key=key)
    else:
        pass  # TODO Print something

    node.children = [order_tree(child, ordering_dict, track=track + [child.name])
                     for child in node.children]
    return node


def paginate(items, items_per_page):
    result = []
    for i in range(0, len(items), items_per_page):
        result.append(items[i:i + items_per_page])
    return result


def paginate_tree(node, pagination_dict, track=[]):
    key = '/'.join(track + ['*'])
    items_per_page = pagination_dict.get(key)

    if items_per_page:
        pages = paginate(node.children, items_per_page)
        
        node.children = []
        for index, page_items in enumerate(pages, start=1):
            page = Node(node.source_dir, 'page%i' % index)
            for item in page_items:
                page.add_child(item)
            node.add_child(page)

    node.children = [
        paginate_tree(child, pagination_dict, track=track + [child.name])
        for child in node.children]
    return node


def track_to_path(track):
    cleaned_track = [part for part in track if part not in ('page1',)]
    return '/'.join(cleaned_track) 


def read_context(dir_, language=None):
    context = {}

    md_files = yield_files(dir_, language and '.%s.md' % language or '.md')
    for md_file in md_files:
        var_name, suffix = os.path.basename(md_file.name).split('.', 1)
        context[var_name] = markdown.markdown(md_file.read())

    yaml_files = yield_files(dir_, language and '.%s.yaml' % language or '.yaml')
    for yaml_file in yaml_files:
        data = yaml.load(yaml_file.read())
        if data:
            context.update(data)

    return context


def fill_tree(node, language=None, track=[]):
    child_contexts = []
    for child in node.children:
        fill_tree(child, language=language, track=track + [child.name])
        child_contexts.append(child.context)

    path = track_to_path(track)
    context = {
        'NAME': node.name,
        'PATH': path,
        'LANGUAGE': language,
        'CHILDREN': child_contexts,
    }

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
    
    context.update(read_context(node.source_dir, language=language))
    node.context = context
    return node


def build_tree(jinja2_env, build_dir, node, root=None, track=[]):
    for child in node.children:
        build_tree(jinja2_env, build_dir, child,
                   root=root or node, track=track + [child.name])

    if node.name == 'ROOT':
        return

    path = track_to_path(track)
    target_dir = os.path.join(
        build_dir, path_for(path, language=node.context['LANGUAGE']))
    target_filename = os.path.join(target_dir, 'index.html')

    if os.path.exists(target_filename):
        return

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    template = jinja2_env.get_template(settings.LAYOUTS[path])
    with codecs.open(target_filename, 'w', 'utf-8') as target_file:
        target_file.write(template.render(ROOT=root.context, **node.context))


def build_(build_dir, language=None):
    translations = None
    if language:
        translations_path = 'translations/%s.po' % language
        if os.path.exists(translations_path):
            translations = get_translations(translations_path)

    assets_env = create_assets_env('static', build_dir, settings.BUNDLES)
    jinja2_env = create_jinja2_env(translations=translations, assets_env=assets_env)

    tree = create_tree('./pages', 'ROOT')
    tree = order_tree(tree, settings.ORDERING)
    tree = paginate_tree(tree, settings.PAGINATION)
    tree = fill_tree(tree, language=language)
    build_tree(jinja2_env, build_dir, tree)


def build(build_dir):
    if settings.LANGUAGES:
        for language in settings.LANGUAGES:
            build_(build_dir, language=language)
    else:
        build_(build_dir)
