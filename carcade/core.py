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
    """Node of the site tree.

    .. attribute:: name

       Name.

    .. attribute:: children

       List of child nodes.

    .. attribute:: source_dir

       Path of the directory reflected by this node.

    .. attribute:: parent

       Parent node.
    """

    def __init__(self, source_dir, name):
        self.name = name
        self.children = []
        self.source_dir = source_dir
        self.parent = None

    def add_child(self, node):
        """Adds `node` to the child nodes."""
        self.children.append(node)
        node.parent = self

    def get_child(self, name):
        """First tries to find and return immediate child called `name`.
        Then continues search by calling `get_child` on every immediate
        child :class:`PageNode`.
        If nothing found, returns ``None``.
        """
        for child in self.children:
            if child.name == name:
                return child

        for child in self.children:
            if not isinstance(child, PageNode):
                continue
            page_child = child.get_child(name)
            if page_child:
                return page_child

    def find_descendant(self, path):
        """Returns descendant node identified by `path`.
        If nothing found, returns ``None``.
        """
        if '/' in path:
            child_name, rest = path.split('/', 1)
            child = self.get_child(child_name)
            return child and child.find_descendant(rest)
        else:
            return self.get_child(path)

    def get_slug(self, intermediate=False):
        """Returns node slug -- string used to build page URL.

        Slug can vary depend on where it's going to be used: in the middle
        of the URL (in that case `intermediate` is ``True``) or in the end
        (`intermediate` is  ``False``).
        """
        if self.name == 'ROOT' or self.get_path() == settings.DEFAULT_PAGE:
            return ''
        return self.name

    def get_path(self):
        """Returns node path."""
        names = []
        node = self
        while node.parent:
            names.append(node.name)
            node = node.parent
        return '/'.join(reversed(names))

    def get_slugs(self):
        """Returns ancestor nodes slugs ordered from top (root)
        to bottom (this node).
        """
        slugs = []
        intermediate = False
        node = self
        while node.parent:
            slugs.append(node.get_slug(intermediate=intermediate))
            intermediate = True
            node = node.parent
        return reversed(slugs)


class PageNode(Node):
    """Represents pages created during automatic pagination
    (see :func:`paginate_tree`). Subclasses :class:`Node`.

    .. attribute:: index

       1-based index.
    """

    def __init__(self, source_dir, index):
        self.index = index
        super(PageNode, self).__init__(source_dir, settings.PAGE_NAME % index)

    def get_slug(self, intermediate=False):
        """If node represents first page or if slug going to be used in
        the middle of the URL, returns empty string.
        Otherwise returns node name.
        """
        if self.index == 1 or intermediate:
            return ''
        return super(PageNode, self).get_slug()


def create_tree(page_dir, page_name):
    """Creates tree that reflects the structure of `page_dir`."""
    node = Node(page_dir, page_name)

    for subpage_name in os.listdir(page_dir):
        subpage_dir = os.path.join(page_dir, subpage_name)
        if os.path.isdir(subpage_dir):
            child = create_tree(subpage_dir, subpage_name)
            node.add_child(child)

    return node


def sort_tree(node, ordering_dict):
    """Recursively sorts the tree according to the `ordering_dict` --
    a dictionary where keys are node paths and values are the following:

    1. ``'alphabetically'``: children will be sorted by their names
    2. ``names list``: children will be sorted in the order in which their
       names appear in the list (see :func:`utils.sort`)
    3. ``callable``: will be called with list of children and must
       return it sorted.
    """
    path = node.get_path()
    key = path or '*'
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
    """Recursively paginates tree according to the `pagination_dict` --
    a dictionary where keys are node paths and values are the numbers of
    the items per page (let's denote it `n`).

    If `node` path is in `pagination_dict`, it's children detached
    from it, split into the chunks of size `n` and then each chunk
    attached back to the `node` through intermediate :class:`PageNode`.
    """
    path = node.get_path()
    key = path or '*'
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
    """Recursively walks the tree and annotates each node with context.

    Calls :func:`utils.read_context` and combines it's result with the
    following data:

    * ``NAME``: `node.name`;
    * ``PATH``: `node.get_path()`;
    * ``LANGUAGE``: `language`;
    * ``CHILDREN``: list of the child contexts;
    * ``SIBLINGS``: list of the sibling contexts;
    * ``PARENT``: parent's context;
    * ``PREV_SIBLING``, ``NEXT_SIBLING``: adjacent siblings contexts.
    """
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
    """Given the site tree, builds the site. The main steps are the following:

    1. Build chidren subtrees;
    2. Determine `index.html` directory (which is basically
       `build_dir`-related url of `node`);
    3. Define which template to use based on a `LAYOUTS` setting;
    4. Render template with node context and write result to `index.html`.
    """
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
        layout_key = node.parent.get_path()
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
    """
    1. Creates the tree from `source_dir` (:func:`create_tree`),
       sorts it (:func:`sort_tree`), paginates (:func:`paginate_tree`) and
       fills with contexts in given `language` (:func:`fill_tree`);
    2. Tries to load translation from `./translations/<language>.po`;
    3. Creates Jinja2 environment with webassets and i18n extensions and
       passes it to :func:`build_site`.
    """
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
    except:
        shutil.rmtree(build_dir)
        raise
