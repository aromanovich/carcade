Settings
========

* .. _languages-setting:

  .. describe:: LANGUAGES = None

  Enables i18n. Must contain a list of site languages.
  Example: ``['ru', 'en']``

* .. _default-language-setting:
  
  .. describe:: DEFAULT_LANGUAGE = None
  
  Language that will be available without it's URL prefix.

* .. describe:: DEFAULT_PAGE = None

  Path of the page that will be avalable at root URL.

* .. _bundles-setting:
  
  .. describe:: BUNDLES = {}

  Dictionary with webassets bundles (:class:`webassets.Bundle`).

* .. _layouts-setting:

  .. describe:: LAYOUTS = {}

  Dictionary (or :class:`patterns`) that maps node paths to their layouts.

* .. _ordering-setting:

  .. describe:: ORDERING = {}

  Dictionary (or :class:`patterns`) that maps node paths to the ordering settings.
  
  Dictionary keys (node paths) are pointing to the nodes whose children needs to be ordered.
  Note: to specify ordering for first level nodes, use key ``'*'`` (because the root node
  doesn't have a path).
  
  This setting passed directly to the :func:`core.sort_tree` -- see it's documentation for 
  variants of ordering.

  Example:

  ::

    ORDERING = {
        '*': ['home', 'about', 'articles'],
        'articles': 'alphabetically',
    }

* .. _pagination-setting:

  .. describe:: PAGINATION = {}

  Dictionary (or :class:`patterns`) that maps node paths to the numbers of children per page.
  
  Dictionary keys (node paths) are pointing to the nodes whose children needs to be divided
  into pages.
  Note: to paginate first level nodes, use key ``'*'`` (because the root node
  doesn't have a path).

  This setting passed directly to the :func:`core.paginate_tree` -- see it's documentation for details.

  Example:

  ::

    PAGINATION = {
        'company/blog': 10,
    }

* .. describe:: PAGE_NAME = 'page%i'

  Slug to be used in the URLs of paginated items.
