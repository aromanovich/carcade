Overview
========

Installation
------------
Carcade is available on PyPI:

  ::
    
    $ pip install carcade

Project structure
-----------------
``carcade init <name>`` creates a brand-new project that contains the following entries:

- | ``pages/`` --
  | is where the source data stored. Data stored in Markdown- and YAML-files and must be
    arranged in folders (probably nested), one folder per site page;
- | ``layouts/`` --
  | folder that contains Jinja2 templates;
- | ``static/`` --
  | content from this folder is just copied into the output directory before build;
- | ``translations/`` --
  | folder for `.po`-files containing translated messages;
- | ``settings.py`` --
  | the project settings. 

Build process
-------------
The project can be built by ``carcade build`` command.

First, Carcade creates the site tree that reflects the structure of the `pages` folder.
Tree nodes match to the page folders, from which they receive names and contexts.

    Each node has two string values associated to it:

    1. `name` -- page folder name;
    2. | `path` -- specifies the path from the tree root to the given node. Basically it's just node names contatenated using ``/``.
       | For example, first-level nodes have ``path`` equal to ``name``.
       | Second-level nodes have path that looks like ``<name-1>/<name-2>``, and so forth.

Then, if ordering and pagination setting were specified, the site tree gets ordered and paginated.

Now the site tree is ready for build. Carcade traverses the tree bottom-up and
for each node does the following:

1. determines it's root-relative URL (in the most cases it's the just a node path);
2. figures out which template use for render by looking at :ref:`LAYOUTS <layouts-setting>`;
3. renders the template in the node context and stores the result at `<root-relative-URL>/index.html`.

How the source data stored
--------------------------

Source data stored in a Markdown and YAML files. Suppose there is a page called ``home``.
It's source folder may look as follows:

  ::

    home
    ├── examples.yaml
    ├── footer.md
    ├── data.en.yaml
    ├── data.ru.yaml
    ├── summary.en.md
    ├── summary.ru.md
    ├── details.en.md
    └── details.ru.md

Carcade will parse these files in the following order (each subsequent step can
override the data from preceding steps):

1. Markdown files;
2. Language-specific Markdown files (only if i18n enabled);
3. YAML files;
4. Language-specific YAML files (only if i18n enabled).

The data from each Markdown file put into the context under it's separate key
(more exactly, the data from ``<name>[.<language].md`` has the key ``<name>``).
For example, after the step 2, the ``home`` context have ``footer``, ``summary`` and ``details`` keys.

YAML files are supposed to contain dictionaries. These dictionaries are merged into
the existing context one by one.

Layouts
-------
Pages are rendered using Jinja2 with some extensions (webassets and i18n).

Along with the context data, the template always contains the following variables:

* ``NAME``: page name;
* ``PATH``: page path in the site tree;
* ``LANGUAGE``: page language;
* ``CHILDREN``: list of the contexts of the child pages;
* ``PARENT``: parent page context;
* ``SIBLINGS``: list of the sibling pages (note: it includes the current page too);
* ``PREV_SIBLING``: previous sibling page context or `None`;
* ``NEXT_SIBLING``: next sibling page context or `None`;
* ``ROOT``: the tree root context. It's only non-empty field is the ``CHILDREN``,
  because the root node doesn't refer to any real page.

Also you can use:

* ``url_for(page_path, language=None)`` function that returns the root-relative
  URL of the specified page in the given language;
* ``markdown`` filter that renders Markdown. Particularly useful when you store
  some Markdown strings in YAML files and want to render them in template.

Translations
------------
To enable i18n, you have to specify :ref:`LANGUAGES <languages-setting>` settings.
It must contain a list of languages (for example, ``['ru', 'en']``).

If i18n enabled, Carcade will build your site for each listed language separately, and:

1. read language-specific data files (as was described above);
2. | look into the `translations` folder for
     `PO-file <http://www.gnu.org/savannah-checkouts/gnu/gettext/manual/html_node/PO-Files.html>`_
     named ``<language>.po``.
   | It means that you can use ``{% trans %}`` tag and ``_`` function in template.
     Please see the `Jinja2 docs for details <http://jinja.pocoo.org/docs/extensions/#i18n-extension>`_.

To ease creation of translation files, Carcade provides command to extract all the
localizable strings from the templates: ``carcade extract_messages``.

Language versions available at prefixed URLs: ``/ru/page-name``, ``/en/page-name`` and so on.
If you want some language available without prexix, you can specify that language in
:ref:`DEFAULT_LANGUAGE <default-language-setting>` setting.

Static assets management
------------------------
Carcade uses webassets for static files management.

You can specify :ref:`BUNDLES <bundles-setting>` setting -- a dictionary
with bundles (:class:`webassets.Bundle`) as values and bundle names as keys.
Then you can use defined bundles in the templates using ``{% assets %}`` tag.
Please see the
`webassets docs for details <http://webassets.readthedocs.org/en/latest/integration/jinja2.html#using-the-tag>`_. 

Pagination
----------
If :ref:`PAGINATION <pagination-setting>` specified,
Carcade helps you to implement paginated output.

Pagination is done by an insertion of special nodes in the tree --
just like if you would manually inserted ``page_<n>`` folders and put
the necessary pages into them.

It may sound obscure, so take a look
at the :ref:`example <example>` or source code: :py:func:`core.paginate_tree`. :)

Ordering
--------
The site tree is ordered.
That order matters when you iterate through the tree in the template.

You can specify order using :ref:`ORDERING <ordering-setting>` setting.
