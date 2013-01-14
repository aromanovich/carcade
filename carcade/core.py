import os
import glob
import codecs
import os.path

import yaml
import markdown

from carcade.conf import settings
from carcade.utils import path_for
from carcade.environments import create_jinja2_environment, url_for


class Node(object):
    def __init__(self, pages_root, page_dir):
        self.children = []
        self.name = None
        self.ascendant = None
        
        self.source_dir = page_dir
        self.name = os.path.relpath(self.source_dir, pages_root)

        self.ordering = None
        ordering_filepath = os.path.join(self.source_dir, 'ordering.txt')
        if os.path.exists(ordering_filepath):
            with codecs.open(ordering_filepath, 'r', 'utf-8') as ordering_file:
                data = yaml.load(ordering_file.read())
                self.ordering = data.get('ordering')

    def add_child(self, page):
        self.children.append(page)
        page.ascendant = self

    def order(self):
        if isinstance(self.ordering, list):
            def key(page):
                name = self.name and os.path.relpath(page.name, self.name) or page.name
                print self.ordering
                if name in self.ordering:
                    return self.ordering.index(name)
                else:
                    return sys.maxint
            self.children.sort(key=key)

        for child in self.children:
            child.order()

    def render(self, jinja2_env, build_dir):
        for child in self.children:
            child.render(jinja2_env, build_dir)


class Page(Node):
    def __init__(self, pages_root, page_dir, language=None):
        super(Page, self).__init__(pages_root, page_dir)
        self.language = language
        self.context = {
            'PAGE_NAME': self.name
        }

        for md_file in self._data_files('md'):
            var_name, suffix = os.path.basename(md_file.name).split('.', 1)
            self.context[var_name] = markdown.markdown(md_file.read())

        for yaml_file in self._data_files('yaml'):
            data = yaml.load(yaml_file.read())
            if data:
                self.context.update(data)


    def _data_files(self, extension):
        pattern = '*'
        if self.language:
            pattern += '.%s' % self.language
        pattern += '.%s' % extension

        for filename in glob.glob(os.path.join(self.source_dir, pattern)):
            with codecs.open(filename, 'r', 'utf-8') as file_:
                yield file_

    def url(self):
        return url_for(self.name, language=self.language)

    def render(self, jinja2_env, build_dir):
        super(Page, self).render(jinja2_env, build_dir)

        # Retrieve template
        template = jinja2_env.get_template(settings.LAYOUTS[self.name])

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

        node = self
        while node.ascendant:
            node = node.ascendant
        

        context = dict(self.context, **{
            'ROOT': node,
            'PAGE': self,
            'SUBPAGES': subpages,  # TODO Make naming more consistent
            'SIBLINGS': siblings,
            'INDEX': index  # XXX
        })

        target_dir = os.path.join(
            build_dir, path_for(self.name, language=self.language))
        target_filename = os.path.join(target_dir, 'index.html')

        if not os.path.exists(target_dir):
            os.makedirs(target_dir)

        with codecs.open(target_filename, 'w', 'utf-8') as target_file:
            target_file.write(template.render(**context))


def create_tree(pages_root, language=None):
    # Build site tree from down to top
    forest = {}  # `forest` contains growing site subtrees
    for page_dir, dirs, files in os.walk(pages_root, topdown=False):
        if page_dir == pages_root:
            # Reached the top. We're done
            break

        page = Page(pages_root, page_dir, language=language)
        for dir_ in dirs:
            subpage_dir = os.path.join(page_dir, dir_)
            subpage = forest.pop(subpage_dir)  # Pop subtree from `forest`
            page.add_child(subpage)  # Attach it to ascendant page

        forest[page_dir] = page  # Put resulting subtree to the `forest`

    root = Node(pages_root, pages_root)
    for page in forest.values():
        root.add_child(page)
    return root


def build(build_dir):
    for language in settings.LANGUAGES:
        jinja2_env = create_jinja2_environment(build_dir, language=language)
        root = create_tree('./pages/', language=language)
        root.order()
        root.render(jinja2_env, build_dir)
