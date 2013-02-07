import os
import glob
import subprocess
import codecs
import itertools

import yaml
import markdown

from carcade.conf import settings


def sh(shell_command):
    subprocess.call(shell_command, shell=True)


def sort(list_, order, key=None):
    """Sorts `list_` by explicitly specified `order`.

    >>> sort(['a', 'b', 'c'],
    ...      ['c', 'b', 'xxx', 'a', 'yyy'])
    ['c', 'b', 'a']

    >>> sort(['a', 'b', 'c', 'd'],
    ...      ['c', 'b', 'a'])
    ['c', 'b', 'a', 'd']

    >>> sort([('a', 1), ('b', 2)],
    ...      ['b', 'a'],
    ...      key=lambda el: el[0])  # Sort tuples by first element
    [('b', 2), ('a', 1)]
    """
    def key_(el):
        k = key(el) if key else el
        if k in order:
            return order.index(k)
        else:
            return len(order) + 1
    return sorted(list_, key=key_)


def paginate(items, items_per_page):
    """Splits `items` list into lists of size `items_per_page`.

    >>> paginate([1, 2, 3], 1)
    [[1], [2], [3]]

    >>> paginate([1, 2, 3, 4, 5, 6, 7], 3)
    [[1, 2, 3], [4, 5, 6], [7]]
    
    >>> paginate([], 3)
    []
    """
    result = []
    for i in range(0, len(items), items_per_page):
        result.append(items[i:i + items_per_page])
    return result


def yield_files(dir_, suffix):
    """Yiels files from `directory` which name ends with `suffix`."""
    for filename in glob.glob(os.path.join(dir_, '*' + suffix)):
        with codecs.open(filename, 'r', 'utf-8') as file_:
            yield file_


def read_context(dir_, language=None):
    """Searches `dir_` for markdown- and yaml-files and returns context
    dictionary with parsed data.

    Markdown- and yaml-files are files which names matched to ``<name>.(md|yaml)``
    or ``<name>.<language>.(md|yaml)`` pattern if `language` specified.

    First parses each markdown-file and puts result into context under the
    `<name>` key. Then parses each yaml-file and updates context with resulting
    dictionary (note: update will override markdown data if there are duplicate keys).
    """
    context = {}

    md_files = yield_files(dir_, '.md')
    if language:
        lang_specific_md_files = yield_files(dir_, '.%s.md' % language)
        md_files = itertools.chain(md_files, lang_specific_md_files)
    for md_file in md_files:
        var_name, suffix = os.path.basename(md_file.name).split('.', 1)
        context[var_name] = markdown.markdown(md_file.read(), ['extra'])

    yaml_files = yield_files(dir_, '.yaml')
    if language:
        lang_specific_yaml_files = yield_files(dir_, '.%s.yaml' % language)
        yaml_files = itertools.chain(yaml_files, lang_specific_yaml_files)
    for yaml_file in yaml_files:
        data = yaml.load(yaml_file.read())
        if data:
            context.update(data)

    return context


def get_template_source(jinja2_env, template):
    """Returns the source text of the given `template`."""
    template_source, _, _ = \
        jinja2_env.loader.get_source(jinja2_env, template)
    return template_source
